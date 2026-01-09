"""
Google Sheets exporter for job listings.
Creates a new sheet for each day with job results.
Supports both file-based and environment variable credentials for cloud deployment.
"""

import os
import json
from datetime import datetime
from typing import List, Set, Optional

import gspread
from google.oauth2.service_account import Credentials

from scrapers.base_scraper import Job


class GoogleSheetsExporter:
    """Exports job listings to a Google Sheets spreadsheet with daily sheets."""
    
    # Required scopes for Google Sheets API
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # Column headers (matching Excel exporter)
    HEADERS = [
        "Job Title",
        "Company", 
        "Location",
        "Salary",
        "Good Tech Found",
        "Bad Tech Found",
        "Bad Tech Count",
        "Score",
        "Platform",
        "Date Posted",
        "Job Link",
    ]
    
    def __init__(
        self, 
        credentials_path: str = None, 
        spreadsheet_id: str = None,
        credentials_json: Optional[str] = None
    ):
        """
        Initialize the Google Sheets exporter.
        
        Args:
            credentials_path: Path to service account JSON credentials file
            spreadsheet_id: Google Sheet ID from the spreadsheet URL
            credentials_json: Optional JSON string of credentials (for serverless)
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.credentials_json = credentials_json
        self.client = None
        self.spreadsheet = None
        
        self._authenticate()
    
    def _authenticate(self):
        """
        Authenticate with Google Sheets API using service account.
        Supports both file-based and inline JSON credentials.
        """
        credentials = None
        
        # Option 1: Use inline JSON credentials (for Azure Functions / AWS Lambda)
        if self.credentials_json:
            try:
                creds_dict = json.loads(self.credentials_json)
                credentials = Credentials.from_service_account_info(
                    creds_dict,
                    scopes=self.SCOPES
                )
                print("[GoogleSheets] Authenticated using inline JSON credentials")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid credentials JSON: {e}")
        
        # Option 2: Use credentials file path (for local development)
        elif self.credentials_path and os.path.exists(self.credentials_path):
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            print("[GoogleSheets] Authenticated using credentials file")
        
        else:
            raise FileNotFoundError(
                "No valid credentials found. Provide either credentials_path "
                "or credentials_json (for serverless environments)."
            )
        
        self.client = gspread.authorize(credentials)
        self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        
        print(f"[GoogleSheets] Connected to: {self.spreadsheet.title}")
    
    def _get_time_period(self) -> str:
        """
        Get the current time period based on hour.
        Morning: 5 AM - 11:59 AM
        Afternoon: 12 PM - 5:59 PM
        Evening: 6 PM - 4:59 AM
        """
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 18:
            return "Afternoon"
        else:
            return "Evening"
    
    def _get_or_create_daily_sheet(self) -> gspread.Worksheet:
        """
        Get or create a worksheet for today's date.
        
        Returns:
            Worksheet named like '2026-01-09'
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Check if sheet for today already exists
        existing_sheets = [ws.title for ws in self.spreadsheet.worksheets()]
        
        if today in existing_sheets:
            print(f"[GoogleSheets] Using existing sheet: {today}")
            worksheet = self.spreadsheet.worksheet(today)
        else:
            print(f"[GoogleSheets] Creating new sheet: {today}")
            worksheet = self.spreadsheet.add_worksheet(
                title=today,
                rows=1000,
                cols=len(self.HEADERS)
            )
            # Write headers to new sheet
            worksheet.update('A1', [self.HEADERS])
            
            # Format header row (bold)
            worksheet.format('A1:K1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.6},
                'horizontalAlignment': 'CENTER'
            })
        
        return worksheet
    
    def _job_to_row(self, job: Job) -> list:
        """Convert a Job object to a row of values."""
        good_tech_str = ", ".join(job.good_tech_found) if job.good_tech_found else "None"
        bad_tech_str = ", ".join(job.bad_tech_found) if job.bad_tech_found else "None"
        
        return [
            job.title,
            job.company,
            job.location,
            job.salary or "Not specified",
            good_tech_str,
            bad_tech_str,
            len(job.bad_tech_found),
            job.score,
            job.platform,
            job.date_posted or "Unknown",
            job.url or "No link available",
        ]
    
    def export(self, jobs: List[Job], filename: str = None) -> str:
        """
        Export jobs to the daily sheet in Google Sheets.
        Adds a section divider for each run (Morning/Afternoon/Evening).
        
        Args:
            jobs: List of Job objects to export
            filename: Ignored (kept for API compatibility with ExcelExporter)
            
        Returns:
            URL to the Google Sheet
        """
        if not jobs:
            print("[GoogleSheets] No jobs to export")
            return self.spreadsheet.url
        
        worksheet = self._get_or_create_daily_sheet()
        
        # Get existing row count (to append after existing data)
        existing_values = worksheet.get_all_values()
        start_row = len(existing_values) + 1
        
        # Create section divider row
        time_period = self._get_time_period()
        current_time = datetime.now().strftime("%I:%M %p")
        divider_text = f"═══ {time_period} Run ({current_time}) - {len(jobs)} jobs ═══"
        divider_row = [divider_text] + [""] * (len(self.HEADERS) - 1)
        
        # Prepare all rows (divider + jobs)
        rows = [divider_row] + [self._job_to_row(job) for job in jobs]
        
        # Batch update for efficiency
        if rows:
            end_row = start_row + len(rows) - 1
            range_str = f'A{start_row}:K{end_row}'
            worksheet.update(range_str, rows)
            
            # Format the divider row
            try:
                worksheet.format(f'A{start_row}:K{start_row}', {
                    'textFormat': {'bold': True, 'fontSize': 11},
                    'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95},
                    'horizontalAlignment': 'CENTER'
                })
                # Merge the divider cells
                worksheet.merge_cells(f'A{start_row}:K{start_row}')
            except Exception as e:
                print(f"[GoogleSheets] Warning: Could not format divider: {e}")
            
            # Apply score-based conditional formatting for new rows
            self._apply_score_formatting(worksheet, start_row, end_row)
        
        print(f"[GoogleSheets] Exported {len(jobs)} jobs to sheet: {worksheet.title}")
        print(f"[GoogleSheets] URL: {self.spreadsheet.url}")
        
        return self.spreadsheet.url
    
    def _apply_score_formatting(self, worksheet: gspread.Worksheet, 
                                 start_row: int, end_row: int):
        """Apply conditional formatting based on score values."""
        # Note: Full conditional formatting requires the Sheets API directly
        # For now, we just format cells nicely
        try:
            worksheet.format(f'A{start_row}:K{end_row}', {
                'horizontalAlignment': 'LEFT',
                'verticalAlignment': 'MIDDLE',
                'wrapStrategy': 'WRAP'
            })
        except Exception as e:
            print(f"[GoogleSheets] Warning: Could not apply formatting: {e}")
    
    def load_existing_job_keys(self) -> Set[tuple]:
        """
        Load existing job keys (company + title) from all sheets.
        Used to prevent adding duplicate jobs across runs.
        
        Returns:
            Set of (company, title) tuples
        """
        existing_keys = set()
        
        try:
            for worksheet in self.spreadsheet.worksheets():
                # Skip sheets that don't look like date sheets
                if not worksheet.title[0].isdigit():
                    continue
                
                values = worksheet.get_all_values()
                
                # Skip header row, read company (col 2) and title (col 1)
                for row in values[1:]:  # Skip header
                    if len(row) >= 2 and row[0] and row[1]:
                        title = str(row[0]).lower().strip()
                        company = str(row[1]).lower().strip()
                        existing_keys.add((company, title))
            
            print(f"[GoogleSheets] Found {len(existing_keys)} existing jobs in spreadsheet")
            
        except Exception as e:
            print(f"[GoogleSheets] Could not load existing jobs: {e}")
        
        return existing_keys

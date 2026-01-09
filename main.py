"""
Auto Job Applier - Main Runner Script

Searches for jobs across configured platforms, filters by tech stack,
and exports results to an Excel file.
"""

import sys
import os
import re
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openpyxl import load_workbook

from config.tech_stacks import (
    JOB_TITLES, 
    LOCATION, 
    REMOTE_ONLY, 
    POSTED_WITHIN_HOURS,
    MIN_SALARY,
    EXCLUDED_JOB_TYPES
)
from config.google_sheets_config import (
    GOOGLE_SHEETS_ENABLED,
    SPREADSHEET_ID,
    CREDENTIALS_PATH,
    CREDENTIALS_JSON
)
from scrapers.google_jobs_scraper import GoogleJobsScraper
from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.indeed_scraper import IndeedScraper
from scrapers.dice_scraper import DiceScraper
from utils.tech_matcher import TechMatcher
from utils.excel_exporter import ExcelExporter
from utils.google_sheets_exporter import GoogleSheetsExporter


# Excel file path (fixed name, overwrites each run but keeps new jobs only)
EXCEL_OUTPUT_PATH = "output/jobs.xlsx"


def load_existing_job_keys(filepath: str) -> set:
    """
    Load existing job keys (company + title) from the Excel file.
    Used to prevent adding duplicate jobs across runs.
    """
    existing_keys = set()
    
    if not os.path.exists(filepath):
        return existing_keys
    
    try:
        wb = load_workbook(filepath, read_only=True)
        ws = wb.active
        
        # Skip header row, read company (col 2) and title (col 1)
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[0] and row[1]:  # title and company
                title = str(row[0]).lower().strip()
                company = str(row[1]).lower().strip()
                existing_keys.add((company, title))
        
        wb.close()
        print(f"[Load] Found {len(existing_keys)} existing jobs in {filepath}")
        
    except Exception as e:
        print(f"[Load] Could not load existing jobs: {e}")
    
    return existing_keys


def filter_existing_jobs(jobs: list, existing_keys: set) -> list:
    """Filter out jobs that already exist in the Excel file."""
    if not existing_keys:
        return jobs
    
    new_jobs = []
    for job in jobs:
        job_key = (job.company.lower().strip(), job.title.lower().strip())
        if job_key not in existing_keys:
            new_jobs.append(job)
    
    skipped = len(jobs) - len(new_jobs)
    if skipped > 0:
        print(f"[Existing] Skipped {skipped} jobs that already exist in Excel")
    
    return new_jobs


def parse_date_posted(date_str: str) -> int:
    """
    Parse date posted string to a sortable number (hours ago).
    Lower number = more recent.
    """
    if not date_str:
        return 9999  # Unknown dates go to the end
    
    date_lower = date_str.lower()
    
    # Match patterns like "2 hours ago", "3 days ago", etc.
    hours_match = re.search(r'(\d+)\s*hour', date_lower)
    if hours_match:
        return int(hours_match.group(1))
    
    days_match = re.search(r'(\d+)\s*day', date_lower)
    if days_match:
        return int(days_match.group(1)) * 24
    
    weeks_match = re.search(r'(\d+)\s*week', date_lower)
    if weeks_match:
        return int(weeks_match.group(1)) * 24 * 7
    
    months_match = re.search(r'(\d+)\s*month', date_lower)
    if months_match:
        return int(months_match.group(1)) * 24 * 30
    
    # Handle special cases
    if 'today' in date_lower or 'just now' in date_lower:
        return 0
    if 'yesterday' in date_lower:
        return 24
    
    return 9999


def sort_jobs_by_date(jobs: list) -> list:
    """Sort jobs by date posted, newest first."""
    return sorted(jobs, key=lambda j: parse_date_posted(j.date_posted))


def filter_by_date_posted(jobs: list, max_hours: int = 24) -> list:
    """
    Strictly filter out jobs that are older than max_hours.
    This is a POST-PROCESSING filter to remove outdated jobs that 
    slipped through the scraper's date filters.
    """
    filtered = []
    
    for job in jobs:
        hours_ago = parse_date_posted(job.date_posted)
        
        if hours_ago <= max_hours:
            filtered.append(job)
        else:
            print(f"[Date Filter] Excluded: {job.title} at {job.company} "
                  f"(Posted: {job.date_posted}, {hours_ago}h ago > {max_hours}h limit)")
    
    removed = len(jobs) - len(filtered)
    if removed > 0:
        print(f"[Date Filter] Removed {removed} jobs older than {max_hours} hours")
    
    return filtered


def parse_salary(salary_str: str) -> int:
    """
    Extract numeric salary value from salary string.
    
    Handles formats like:
    - "$120,000 - $150,000 a year"
    - "$140K - $180K"
    - "$150,000/yr"
    - "US$120,000"
    """
    if not salary_str:
        return 0
    
    import re
    
    # Look for patterns like $120,000 or $120K or US$120K
    matches = re.findall(r'(?:US)?\$[\d,]+(?:K)?', salary_str, re.IGNORECASE)
    
    if not matches:
        return 0
    
    # Take the first (usually minimum) salary
    salary = matches[0].replace('$', '').replace(',', '').replace('US', '')
    
    if salary.upper().endswith('K'):
        return int(float(salary[:-1]) * 1000)
    
    return int(float(salary))


def is_usd_salary(salary_str: str) -> bool:
    """
    Check if salary is in USD (not other currencies like SGD, EUR, etc.)
    Returns True if USD or if no salary specified.
    """
    if not salary_str:
        return True  # No salary = don't filter out
    
    salary_lower = salary_str.lower()
    
    # List of non-USD currency indicators
    non_usd_indicators = [
        'sgd', 'eur', 'gbp', 'cad', 'aud', 'inr', 'jpy', 
        '€', '£', '¥', 'rs', 'pkr', 'aed', 'chf',
        'singapore', 'euro', 'pound', 'rupee'
    ]
    
    for indicator in non_usd_indicators:
        if indicator in salary_lower:
            return False
    
    # Check if it has $ or US$ (USD indicators)
    if '$' in salary_str or 'usd' in salary_lower:
        return True
    
    # If contains numbers but no currency symbol, it's ambiguous - accept it
    return True


def filter_by_salary(jobs: list, min_salary: int) -> list:
    """Filter jobs that meet minimum salary requirement and are in USD."""
    filtered = []
    
    for job in jobs:
        # First check if it's USD
        if not is_usd_salary(job.salary):
            print(f"[Currency Filter] Excluded: {job.title} at {job.company} "
                  f"(Non-USD: {job.salary})")
            continue
        
        salary_value = parse_salary(job.salary)
        
        # Include jobs with no salary listed (we don't want to exclude them)
        # Only filter out jobs that explicitly show a salary below minimum
        if salary_value == 0 or salary_value >= min_salary:
            filtered.append(job)
        else:
            print(f"[Salary Filter] Excluded: {job.title} at {job.company} "
                  f"(Salary: {job.salary} < ${min_salary:,})")
    
    return filtered


def deduplicate_jobs(jobs: list) -> list:
    """Remove duplicate jobs based on company + title."""
    seen = set()
    unique_jobs = []
    
    for job in jobs:
        job_key = (job.company.lower().strip(), job.title.lower().strip())
        if job_key not in seen:
            seen.add(job_key)
            unique_jobs.append(job)
    
    duplicates_removed = len(jobs) - len(unique_jobs)
    if duplicates_removed > 0:
        print(f"[Dedup] Removed {duplicates_removed} duplicate jobs")
    
    return unique_jobs


def filter_excluded_jobs(jobs: list) -> list:
    """
    Filter out jobs that match excluded keywords.
    Removes: entry level, internships, equity-based, non-US locations.
    """
    filtered = []
    
    for job in jobs:
        # Combine title, company, location, and description for checking
        text_to_check = f"{job.title} {job.company} {job.location} {job.description}".lower()
        
        excluded = False
        for keyword in EXCLUDED_JOB_TYPES:
            if keyword.lower() in text_to_check:
                print(f"[Job Type Filter] Excluded: {job.title} at {job.company} "
                      f"(matched: '{keyword}')")
                excluded = True
                break
        
        if not excluded:
            filtered.append(job)
    
    return filtered


def filter_us_remote_only(jobs: list) -> list:
    """
    Ensure jobs are actually US-based and remote.
    Checks title, description, and location for onsite/hybrid indicators.
    """
    filtered = []
    
    # Non-US location indicators
    non_us_indicators = [
        'uk', 'united kingdom', 'london', 'europe', 'eu only',
        'india', 'bangalore', 'hyderabad', 'mumbai', 'delhi', 'chennai',
        'pakistan', 'lahore', 'karachi', 'islamabad',
        'canada', 'toronto', 'vancouver', 'montreal',
        'australia', 'sydney', 'melbourne',
        'singapore', 'philippines', 'manila', 'nigeria', 'lagos',
        'germany', 'berlin', 'france', 'paris', 'spain', 'madrid',
        'brazil', 'mexico', 'argentina', 'latam'
    ]
    
    # Onsite/hybrid indicators (exclude these jobs)
    onsite_indicators = [
        'onsite', 'on-site', 'on site',
        'hybrid', 'in-office', 'in office',
        'office-based', 'office based',
        'must be local', 'local candidates',
        'relocation required', 'no remote',
        'not remote', 'onsite required'
    ]
    
    for job in jobs:
        location = job.location.lower() if job.location else ''
        title = job.title.lower() if job.title else ''
        description = job.description.lower() if job.description else ''
        
        # Combine all text for checking
        all_text = f"{title} {location} {description}"
        
        # Check if location indicates non-US
        is_non_us = False
        for indicator in non_us_indicators:
            if indicator in location:
                is_non_us = True
                break
        
        if is_non_us:
            print(f"[Location Filter] Excluded: {job.title} at {job.company} "
                  f"(Non-US location: {job.location})")
            continue
        
        # Check for onsite/hybrid in title, location, or description
        is_onsite = False
        matched_indicator = None
        for indicator in onsite_indicators:
            if indicator in title or indicator in location:
                is_onsite = True
                matched_indicator = indicator
                break
        
        if is_onsite:
            print(f"[Remote Filter] Excluded: {job.title} at {job.company} "
                  f"(Found '{matched_indicator}')")
            continue
        
        filtered.append(job)
    
    return filtered


def main():
    """Main entry point for the job scraper."""
    print("=" * 60)
    print("Auto Job Applier - Job Scraper (HEADLESS MODE)")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Initialize exporter based on configuration
    sheets_exporter = None
    if GOOGLE_SHEETS_ENABLED:
        print("\n[Init] Google Sheets export ENABLED")
        print("[Init] Connecting to Google Sheets...")
        sheets_exporter = GoogleSheetsExporter(
            credentials_path=CREDENTIALS_PATH,
            spreadsheet_id=SPREADSHEET_ID,
            credentials_json=CREDENTIALS_JSON
        )
        existing_job_keys = sheets_exporter.load_existing_job_keys()
    else:
        print("\n[Init] Using local Excel export")
        print("[Init] Loading existing jobs from Excel...")
        existing_job_keys = load_existing_job_keys(EXCEL_OUTPUT_PATH)
    
    # Initialize components
    google_scraper = None
    linkedin_scraper = None
    indeed_scraper = None
    dice_scraper = None
    all_jobs = []
    
    try:
        # ==================== GOOGLE JOBS ====================
        print("\n" + "=" * 60)
        print("📌 GOOGLE JOBS SEARCH")
        print("=" * 60)
        
        print("\n[Init] Starting Google Jobs scraper...")
        google_scraper = GoogleJobsScraper(headless=True)  # Run in background
        
        print(f"\n[Search] Searching for {len(JOB_TITLES)} job titles...")
        print(f"[Search] Location: {LOCATION}")
        print(f"[Search] Remote Only: {REMOTE_ONLY}")
        print(f"[Search] Posted Within: {POSTED_WITHIN_HOURS} hours")
        print("-" * 60)
        
        for title in JOB_TITLES:
            jobs = google_scraper.search(
                query=title,
                location=LOCATION,
                remote_only=REMOTE_ONLY,
                posted_within_hours=POSTED_WITHIN_HOURS
            )
            all_jobs.extend(jobs)
            print(f"  ✓ {title}: {len(jobs)} jobs found")
        
        google_scraper.close()
        google_scraper = None
        print(f"\n[Google Jobs] Total: {len(all_jobs)} jobs")
        
        # ==================== LINKEDIN ====================
        print("\n" + "=" * 60)
        print("📌 LINKEDIN JOBS SEARCH")
        print("=" * 60)
        
        print("\n[Init] Starting LinkedIn scraper...")
        linkedin_scraper = LinkedInScraper(headless=True)  # Run in background
        
        linkedin_count = 0
        for title in JOB_TITLES:
            jobs = linkedin_scraper.search(
                query=title,
                location=LOCATION,
                remote_only=REMOTE_ONLY,
                posted_within_hours=POSTED_WITHIN_HOURS
            )
            all_jobs.extend(jobs)
            linkedin_count += len(jobs)
            print(f"  ✓ {title}: {len(jobs)} jobs found")
        
        linkedin_scraper.close()
        linkedin_scraper = None
        print(f"\n[LinkedIn] Total: {linkedin_count} jobs")
        
        # ==================== INDEED ====================
        print("\n" + "=" * 60)
        print("📌 INDEED JOBS SEARCH")
        print("=" * 60)
        
        print("\n[Init] Starting Indeed scraper...")
        indeed_scraper = IndeedScraper(headless=True)  # Run in background
        
        indeed_count = 0
        for title in JOB_TITLES:
            jobs = indeed_scraper.search(
                query=title,
                location=LOCATION,
                remote_only=REMOTE_ONLY,
                posted_within_hours=POSTED_WITHIN_HOURS
            )
            all_jobs.extend(jobs)
            indeed_count += len(jobs)
            print(f"  ✓ {title}: {len(jobs)} jobs found")
        
        indeed_scraper.close()
        indeed_scraper = None
        print(f"\n[Indeed] Total: {indeed_count} jobs")
        
        # ==================== DICE ====================
        print("\n" + "=" * 60)
        print("📌 DICE JOBS SEARCH")
        print("=" * 60)
        
        print("\n[Init] Starting Dice scraper...")
        dice_scraper = DiceScraper(headless=True)  # Run in background
        
        dice_count = 0
        for title in JOB_TITLES:
            jobs = dice_scraper.search(
                query=title,
                location=LOCATION,
                remote_only=REMOTE_ONLY,
                posted_within_hours=POSTED_WITHIN_HOURS
            )
            all_jobs.extend(jobs)
            dice_count += len(jobs)
            print(f"  ✓ {title}: {len(jobs)} jobs found")
        
        dice_scraper.close()
        dice_scraper = None
        print(f"\n[Dice] Total: {dice_count} jobs")
        
        print("-" * 60)
        print(f"[Search] Total jobs found: {len(all_jobs)}")
        
        # Deduplicate jobs (within this run)
        print("\n[Processing] Removing duplicates from this run...")
        all_jobs = deduplicate_jobs(all_jobs)
        print(f"[Processing] After deduplication: {len(all_jobs)} jobs")
        
        # Filter jobs that already exist in Excel (from previous runs)
        print("\n[Processing] Filtering already-saved jobs...")
        all_jobs = filter_existing_jobs(all_jobs, existing_job_keys)
        print(f"[Processing] New jobs only: {len(all_jobs)} jobs")
        
        # Filter US remote only
        print("\n[Processing] Filtering for US remote only...")
        all_jobs = filter_us_remote_only(all_jobs)
        print(f"[Processing] After location filter: {len(all_jobs)} jobs")
        
        # Filter excluded job types (entry level, intern, equity)
        print("\n[Processing] Filtering excluded job types...")
        all_jobs = filter_excluded_jobs(all_jobs)
        print(f"[Processing] After job type filter: {len(all_jobs)} jobs")
        
        # Apply tech stack filter
        print("\n[Processing] Applying tech stack filter...")
        matcher = TechMatcher()
        filtered_jobs = matcher.filter_jobs(all_jobs)
        print(f"[Processing] After tech filter: {len(filtered_jobs)} jobs")
        
        # Apply salary filter
        print(f"\n[Processing] Filtering by minimum salary (${MIN_SALARY:,})...")
        filtered_jobs = filter_by_salary(filtered_jobs, MIN_SALARY)
        print(f"[Processing] After salary filter: {len(filtered_jobs)} jobs")
        
        # Strict date filter - remove jobs older than 24 hours
        print(f"\n[Processing] Filtering by date (last {POSTED_WITHIN_HOURS} hours only)...")
        filtered_jobs = filter_by_date_posted(filtered_jobs, POSTED_WITHIN_HOURS)
        print(f"[Processing] After date filter: {len(filtered_jobs)} jobs")
        
        # Sort by date (newest first)
        print("\n[Processing] Sorting by date (newest first)...")
        filtered_jobs = sort_jobs_by_date(filtered_jobs)
        
        # Export jobs
        if filtered_jobs:
            if GOOGLE_SHEETS_ENABLED and sheets_exporter:
                print("\n[Export] Exporting to Google Sheets...")
                sheet_url = sheets_exporter.export(filtered_jobs)
                
                print(f"\n{'=' * 60}")
                print("✅ JOB SEARCH COMPLETE!")
                print(f"{'=' * 60}")
                print(f"Total jobs saved: {len(filtered_jobs)}")
                print(f"Google Sheet: {sheet_url}")
                print(f"{'=' * 60}")
            else:
                print("\n[Export] Generating Excel file...")
                exporter = ExcelExporter(output_dir="output")
                
                # Fixed filename - overwrites previous file each run
                filename = "jobs"
                filepath = exporter.export(filtered_jobs, filename)
                
                print(f"\n{'=' * 60}")
                print("✅ JOB SEARCH COMPLETE!")
                print(f"{'=' * 60}")
                print(f"Total jobs saved: {len(filtered_jobs)}")
                print(f"Excel file: {os.path.abspath(filepath)}")
                print(f"{'=' * 60}")
        else:
            print("\n⚠️ No jobs matched your criteria.")
            print("Try adjusting your filters or search terms.")
        
    except KeyboardInterrupt:
        print("\n\n[Interrupted] Shutting down...")
    except Exception as e:
        print(f"\n[Error] {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up all scrapers
        if google_scraper:
            print("\n[Cleanup] Closing Google browser...")
            google_scraper.close()
        if linkedin_scraper:
            print("\n[Cleanup] Closing LinkedIn browser...")
            linkedin_scraper.close()
        if indeed_scraper:
            print("\n[Cleanup] Closing Indeed browser...")
            indeed_scraper.close()
        if dice_scraper:
            print("\n[Cleanup] Closing Dice browser...")
            dice_scraper.close()
    
    print("\nDone!")


if __name__ == "__main__":
    main()

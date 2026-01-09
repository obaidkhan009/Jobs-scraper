"""
FastAPI Web Dashboard for Job Scraper
Run with: uvicorn app:app --reload
"""

import os
import json
import asyncio
import threading
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import the scraper components
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.tech_stacks import JOB_TITLES, LOCATION, REMOTE_ONLY, POSTED_WITHIN_HOURS, MIN_SALARY
from config.google_sheets_config import GOOGLE_SHEETS_ENABLED, SPREADSHEET_ID

app = FastAPI(title="Job Scraper Dashboard")

# Store for run history and status
RUN_HISTORY_FILE = "run_history.json"
scraper_status = {
    "is_running": False,
    "current_platform": None,
    "progress": 0,
    "message": "Idle",
    "last_run": None
}


def load_run_history():
    """Load run history from JSON file."""
    if os.path.exists(RUN_HISTORY_FILE):
        try:
            with open(RUN_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def save_run_history(history):
    """Save run history to JSON file."""
    with open(RUN_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


def get_time_period():
    """Get current time period (Morning/Afternoon/Evening)."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 18:
        return "Afternoon"
    else:
        return "Evening"


def run_scraper_task():
    """Run the job scraper in background."""
    global scraper_status
    
    try:
        scraper_status["is_running"] = True
        scraper_status["progress"] = 0
        scraper_status["message"] = "Starting scraper..."
        
        # Import scraper modules
        from scrapers.google_jobs_scraper import GoogleJobsScraper
        from scrapers.linkedin_scraper import LinkedInScraper
        from scrapers.indeed_scraper import IndeedScraper
        from scrapers.dice_scraper import DiceScraper
        from utils.tech_matcher import TechMatcher
        from utils.google_sheets_exporter import GoogleSheetsExporter
        from config.google_sheets_config import CREDENTIALS_PATH, CREDENTIALS_JSON
        from main import (
            deduplicate_jobs, filter_existing_jobs, filter_us_remote_only,
            filter_excluded_jobs, filter_by_salary, filter_by_date_posted,
            sort_jobs_by_date
        )
        
        all_jobs = []
        platforms = [
            ("Google Jobs", GoogleJobsScraper),
            ("LinkedIn", LinkedInScraper),
            ("Indeed", IndeedScraper),
            ("Dice", DiceScraper),
        ]
        
        # Initialize Google Sheets exporter
        sheets_exporter = GoogleSheetsExporter(
            credentials_path=CREDENTIALS_PATH,
            spreadsheet_id=SPREADSHEET_ID,
            credentials_json=CREDENTIALS_JSON
        )
        existing_job_keys = sheets_exporter.load_existing_job_keys()
        
        # Parallel scraping function
        def scrape_single_platform(platform_info):
            platform_name, ScraperClass = platform_info
            platform_jobs = []
            try:
                scraper = ScraperClass(headless=True)
                for title in JOB_TITLES:
                    try:
                        jobs = scraper.search(
                            query=title,
                            location=LOCATION,
                            remote_only=REMOTE_ONLY,
                            posted_within_hours=POSTED_WITHIN_HOURS
                        )
                        platform_jobs.extend(jobs)
                    except:
                        continue
                scraper.close()
            except Exception as e:
                print(f"Error scraping {platform_name}: {e}")
            return platform_name, platform_jobs
        
        # Run all scrapers in parallel
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        scraper_status["message"] = "Scraping all platforms in parallel..."
        
        results = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(scrape_single_platform, p): p[0] for p in platforms}
            completed = 0
            for future in as_completed(futures):
                platform_name = futures[future]
                try:
                    name, jobs = future.result()
                    results[name] = jobs
                    all_jobs.extend(jobs)
                    completed += 1
                    scraper_status["progress"] = int((completed / len(platforms)) * 60)
                    scraper_status["message"] = f"Completed {name}: {len(jobs)} jobs"
                except Exception as e:
                    print(f"[{platform_name}] Failed: {e}")
        
        # Filter jobs
        scraper_status["progress"] = 70
        scraper_status["message"] = "Filtering jobs..."
        
        all_jobs = deduplicate_jobs(all_jobs)
        all_jobs = filter_existing_jobs(all_jobs, existing_job_keys)
        all_jobs = filter_us_remote_only(all_jobs)
        all_jobs = filter_excluded_jobs(all_jobs)
        
        matcher = TechMatcher()
        filtered_jobs = matcher.filter_jobs(all_jobs)
        filtered_jobs = filter_by_salary(filtered_jobs, MIN_SALARY)
        filtered_jobs = filter_by_date_posted(filtered_jobs, POSTED_WITHIN_HOURS)
        filtered_jobs = sort_jobs_by_date(filtered_jobs)
        
        # Export to Google Sheets
        scraper_status["progress"] = 90
        scraper_status["message"] = "Exporting to Google Sheets..."
        
        sheet_url = sheets_exporter.export(filtered_jobs)
        
        # Save to run history
        run_record = {
            "timestamp": datetime.now().isoformat(),
            "time_period": get_time_period(),
            "jobs_found": len(all_jobs),
            "jobs_after_filter": len(filtered_jobs),
            "sheet_url": sheet_url
        }
        
        history = load_run_history()
        history.insert(0, run_record)
        history = history[:50]  # Keep last 50 runs
        save_run_history(history)
        
        scraper_status["progress"] = 100
        scraper_status["message"] = f"Complete! Found {len(filtered_jobs)} jobs"
        scraper_status["last_run"] = run_record
        
    except Exception as e:
        scraper_status["message"] = f"Error: {str(e)}"
        
    finally:
        scraper_status["is_running"] = False
        scraper_status["current_platform"] = None


# HTML Template (embedded for simplicity)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Scraper Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        h1 {
            font-size: 2.5rem;
            background: linear-gradient(90deg, #00d4ff, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #94a3b8;
            font-size: 1.1rem;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .card-title {
            font-size: 0.9rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
        }
        
        .card-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #00d4ff;
        }
        
        .card-value.purple { color: #7c3aed; }
        .card-value.green { color: #10b981; }
        .card-value.orange { color: #f59e0b; }
        
        .run-button {
            width: 100%;
            padding: 20px 40px;
            font-size: 1.2rem;
            font-weight: 600;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            background: linear-gradient(90deg, #00d4ff, #7c3aed);
            color: white;
            transition: transform 0.2s, box-shadow 0.2s;
            margin-bottom: 20px;
        }
        
        .run-button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 40px rgba(0, 212, 255, 0.3);
        }
        
        .run-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .status-bar {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
        }
        
        .progress-container {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #7c3aed);
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .status-text {
            text-align: center;
            color: #94a3b8;
        }
        
        .history-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 24px;
        }
        
        .history-title {
            font-size: 1.3rem;
            margin-bottom: 20px;
        }
        
        .history-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .history-table th, .history-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .history-table th {
            color: #94a3b8;
            font-weight: 500;
            font-size: 0.85rem;
            text-transform: uppercase;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .badge-morning { background: #fef3c7; color: #92400e; }
        .badge-afternoon { background: #dbeafe; color: #1e40af; }
        .badge-evening { background: #ede9fe; color: #5b21b6; }
        
        .link-btn {
            color: #00d4ff;
            text-decoration: none;
            font-weight: 500;
        }
        
        .link-btn:hover {
            text-decoration: underline;
        }
        
        .config-info {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        
        .config-item {
            font-size: 0.85rem;
            color: #94a3b8;
        }
        
        .config-item span {
            color: #00d4ff;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Job Scraper Dashboard</h1>
            <p class="subtitle">Automated job search across Google Jobs, LinkedIn, Indeed & Dice</p>
        </header>
        
        <div class="dashboard-grid">
            <div class="card">
                <div class="card-title">Total Runs Today</div>
                <div class="card-value" id="runsToday">0</div>
            </div>
            <div class="card">
                <div class="card-title">Jobs Found (Last Run)</div>
                <div class="card-value purple" id="lastJobCount">0</div>
            </div>
            <div class="card">
                <div class="card-title">Total Jobs This Week</div>
                <div class="card-value green" id="weeklyJobs">0</div>
            </div>
            <div class="card">
                <div class="card-title">Job Titles Searching</div>
                <div class="card-value orange" id="titleCount">{{ job_titles_count }}</div>
            </div>
        </div>
        
        <button class="run-button" id="runBtn" onclick="startScraper()">
            🚀 Run Job Scraper
        </button>
        
        <div class="status-bar">
            <div class="progress-container">
                <div class="progress-bar" id="progressBar" style="width: 0%"></div>
            </div>
            <p class="status-text" id="statusText">Ready to run</p>
        </div>
        
        <div class="config-info">
            <div class="config-item">Location: <span>{{ location }}</span></div>
            <div class="config-item">Remote Only: <span>{{ remote_only }}</span></div>
            <div class="config-item">Min Salary: <span>${{ min_salary | int | format_number }}</span></div>
            <div class="config-item">Posted Within: <span>{{ posted_within }}h</span></div>
        </div>
        
        <div class="history-section" style="margin-top: 30px;">
            <h2 class="history-title">📊 Run History</h2>
            <table class="history-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Period</th>
                        <th>Jobs Found</th>
                        <th>After Filter</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="historyBody">
                    <!-- Populated by JavaScript -->
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        let pollInterval = null;
        
        async function startScraper() {
            const btn = document.getElementById('runBtn');
            btn.disabled = true;
            btn.textContent = '⏳ Running...';
            
            try {
                await fetch('/api/run', { method: 'POST' });
                pollInterval = setInterval(pollStatus, 1000);
            } catch (e) {
                console.error(e);
                btn.disabled = false;
                btn.textContent = '🚀 Run Job Scraper';
            }
        }
        
        async function pollStatus() {
            try {
                const res = await fetch('/api/status');
                const status = await res.json();
                
                document.getElementById('progressBar').style.width = status.progress + '%';
                document.getElementById('statusText').textContent = status.message;
                
                if (!status.is_running) {
                    clearInterval(pollInterval);
                    document.getElementById('runBtn').disabled = false;
                    document.getElementById('runBtn').textContent = '🚀 Run Job Scraper';
                    loadHistory();
                }
            } catch (e) {
                console.error(e);
            }
        }
        
        async function loadHistory() {
            try {
                const res = await fetch('/api/history');
                const history = await res.json();
                
                const tbody = document.getElementById('historyBody');
                tbody.innerHTML = '';
                
                let todayRuns = 0;
                let weeklyJobs = 0;
                const today = new Date().toDateString();
                const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
                
                history.forEach((run, idx) => {
                    const date = new Date(run.timestamp);
                    if (date.toDateString() === today) todayRuns++;
                    if (date > weekAgo) weeklyJobs += run.jobs_after_filter;
                    
                    const badgeClass = run.time_period.toLowerCase();
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${date.toLocaleString()}</td>
                        <td><span class="badge badge-${badgeClass}">${run.time_period}</span></td>
                        <td>${run.jobs_found}</td>
                        <td>${run.jobs_after_filter}</td>
                        <td><a href="${run.sheet_url}" target="_blank" class="link-btn">Open Sheet</a></td>
                    `;
                    tbody.appendChild(tr);
                });
                
                document.getElementById('runsToday').textContent = todayRuns;
                document.getElementById('weeklyJobs').textContent = weeklyJobs;
                
                if (history.length > 0) {
                    document.getElementById('lastJobCount').textContent = history[0].jobs_after_filter;
                }
            } catch (e) {
                console.error(e);
            }
        }
        
        // Load history on page load
        loadHistory();
    </script>
</body>
</html>
'''


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the dashboard."""
    from jinja2 import Environment
    
    # Create environment with custom filter
    env = Environment()
    env.filters['format_number'] = lambda x: f"{int(x):,}"
    
    template = env.from_string(HTML_TEMPLATE)
    
    html = template.render(
        job_titles_count=len(JOB_TITLES),
        location=LOCATION,
        remote_only="Yes" if REMOTE_ONLY else "No",
        min_salary=MIN_SALARY,
        posted_within=POSTED_WITHIN_HOURS
    )
    return HTMLResponse(content=html)


@app.post("/api/run")
async def run_scraper(background_tasks: BackgroundTasks):
    """Start the scraper in background."""
    global scraper_status
    
    if scraper_status["is_running"]:
        return JSONResponse({"error": "Scraper already running"}, status_code=400)
    
    # Run in background thread
    thread = threading.Thread(target=run_scraper_task)
    thread.start()
    
    return {"message": "Scraper started"}


@app.get("/api/status")
async def get_status():
    """Get current scraper status."""
    return scraper_status


@app.get("/api/history")
async def get_history():
    """Get run history."""
    return load_run_history()


@app.get("/api/config")
async def get_config():
    """Get current configuration."""
    return {
        "job_titles": JOB_TITLES,
        "location": LOCATION,
        "remote_only": REMOTE_ONLY,
        "min_salary": MIN_SALARY,
        "posted_within_hours": POSTED_WITHIN_HOURS,
        "google_sheets_enabled": GOOGLE_SHEETS_ENABLED,
        "spreadsheet_id": SPREADSHEET_ID
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

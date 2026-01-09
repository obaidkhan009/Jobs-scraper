# Jobs-Scraper 🔍

Automated job search tool that scrapes jobs from multiple platforms, filters them by your preferences, and exports to Google Sheets.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FastAPI Dashboard (app.py)                   │
│                     http://localhost:8000                           │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         SCRAPING LAYER                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐  │
│  │ Google Jobs  │ │   LinkedIn   │ │    Indeed    │ │    Dice    │  │
│  │   Scraper    │ │   Scraper    │ │   Scraper    │ │  Scraper   │  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘  │
│                     (Selenium + Chrome Headless)                    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FILTERING PIPELINE                           │
│  1. Deduplicate (remove same job from multiple platforms)           │
│  2. Filter existing (skip jobs already in Google Sheet)             │
│  3. Location filter (US only, exclude non-US locations)             │
│  4. Remote filter (exclude onsite/hybrid jobs)                      │
│  5. Tech stack filter (match good tech, exclude bad tech)           │
│  6. Salary filter ($120K+ minimum)                                  │
│  7. Date filter (last 24 hours only)                                │
│  8. Job type filter (exclude entry-level, intern, clearance)        │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         EXPORT LAYER                                │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              Google Sheets API (gspread)                    │    │
│  │  - Daily sheets (YYYY-MM-DD)                                │    │
│  │  - Section dividers (Morning/Afternoon/Evening)             │    │
│  │  - Deduplication across all sheets                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python 3.11+, FastAPI |
| **Web Scraping** | Selenium, Chrome WebDriver |
| **Cloud Export** | Google Sheets API (gspread) |
| **Auth** | Google Service Account |
| **Frontend** | Embedded HTML/CSS/JS (no framework) |

## Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| selenium | ≥4.15.0 | Browser automation for scraping |
| webdriver-manager | ≥4.0.1 | Auto-manage Chrome WebDriver |
| beautifulsoup4 | ≥4.12.2 | HTML parsing (fallback) |
| lxml | ≥4.9.3 | Fast XML/HTML parser |
| requests | ≥2.31.0 | HTTP requests |
| openpyxl | ≥3.1.2 | Excel export (fallback) |
| gspread | ≥5.12.0 | Google Sheets API client |
| google-auth | ≥2.23.0 | Google authentication |
| fastapi | ≥0.104.0 | Web dashboard framework |
| uvicorn | ≥0.24.0 | ASGI server |
| jinja2 | ≥3.1.2 | HTML templating |

## Key Features

- **Multi-Platform Scraping**: Google Jobs, LinkedIn, Indeed, Dice
- **Smart Filtering**: Tech stack matching, salary, remote-only, location
- **Deduplication**: Prevents duplicate jobs across runs (checked against Google Sheet)
- **Daily Organization**: Jobs organized by date with Morning/Afternoon/Evening sections
- **Web Dashboard**: One-click run with progress tracking

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure Google Sheets credentials:**
   - Create a Google Cloud service account
   - Download JSON credentials
   - Place in project root
   - Update `config/google_sheets_config.py`

3. **Configure job preferences** in `config/tech_stacks.py`:
   - Job titles to search
   - Good/bad technologies
   - Minimum salary
   - Location settings

## Usage

### Option 1: Command Line
```bash
python3 main.py
```

### Option 2: Web Dashboard
```bash
python3 -m uvicorn app:app --port 8000
# Open http://localhost:8000
```

## Configuration Files

| File | Purpose |
|------|---------|
| `config/tech_stacks.py` | Job titles, tech preferences, salary, filters |
| `config/google_sheets_config.py` | Google Sheets settings |

## Filtering Logic

Jobs pass through these filters in order:

1. **Deduplication** - Remove duplicate jobs from multiple platforms
2. **Existing Check** - Skip jobs already saved to Google Sheet  
3. **Location** - US only (excludes India, UK, Canada, etc.)
4. **Remote** - Excludes jobs with "onsite", "hybrid", "in-office" in title/location/description
5. **Tech Stack** - Matches your preferred technologies
6. **Salary** - Minimum $120K (configurable)
7. **Date** - Posted within last 24 hours
8. **Job Type** - Excludes entry-level, intern, clearance-required

## Output

Jobs exported to Google Sheets with columns:
- Job Title, Company, Location, Salary
- Good/Bad Tech Found, Match Score
- Platform, Date Posted, Job Link

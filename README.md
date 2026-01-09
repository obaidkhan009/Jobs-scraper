# Jobs-Scraper 🔍

Automated job search tool that scrapes jobs from multiple platforms and exports to Google Sheets.

## Features

- **Multi-Platform Search**: Google Jobs, LinkedIn, Indeed, Dice
- **Smart Filtering**: Tech stack matching, salary, remote-only, location
- **Google Sheets Export**: Daily sheets with Morning/Afternoon/Evening sections
- **Deduplication**: Prevents duplicate jobs across runs

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Add your Google Sheets credentials:
   - Create a service account in Google Cloud Console
   - Download the JSON credentials file
   - Place it in the project root
   - Update `config/google_sheets_config.py` with the filename

3. Configure your preferences in `config/tech_stacks.py`:
   - Job titles to search
   - Good/bad technologies
   - Minimum salary
   - Location settings

## Usage

```bash
python3 main.py
```

Run 3x daily for best results - each run creates a section in the daily sheet.

## Configuration

| File | Purpose |
|------|---------|
| `config/tech_stacks.py` | Job titles, tech preferences, salary, filters |
| `config/google_sheets_config.py` | Google Sheets settings |

## Output

Jobs are exported to your Google Sheet with columns:
- Job Title, Company, Location, Salary
- Good/Bad Tech Found, Score
- Platform, Date Posted, Job Link

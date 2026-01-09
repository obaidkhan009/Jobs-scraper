"""
Google Sheets configuration for job exporter.
Supports environment variables for Azure Functions / AWS Lambda deployment.
"""

import os

# Enable Google Sheets export (set to False to use local Excel file)
# Env var: GOOGLE_SHEETS_ENABLED (set to "true" or "false")
GOOGLE_SHEETS_ENABLED = os.environ.get("GOOGLE_SHEETS_ENABLED", "true").lower() == "true"

# Google Sheet ID from the spreadsheet URL
# Env var: SPREADSHEET_ID
# Example URL: https://docs.google.com/spreadsheets/d/1PhtOrm0J_jN7gjYUSvAhMRfPWBMxu1vZ6ERYjhpPVKc/edit
SPREADSHEET_ID = os.environ.get(
    "SPREADSHEET_ID",
    "1PhtOrm0J_jN7gjYUSvAhMRfPWBMxu1vZ6ERYjhpPVKc"
)

# Path to service account credentials JSON file
# Env var: GOOGLE_CREDENTIALS_PATH (for file path) or GOOGLE_CREDENTIALS_JSON (for inline JSON)
CREDENTIALS_PATH = os.environ.get(
    "GOOGLE_CREDENTIALS_PATH",
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "secure-wharf-483714-d0-b3c27c6b5b1d.json"
    )
)

# For serverless: credentials can be passed as JSON string in env var
CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON", None)

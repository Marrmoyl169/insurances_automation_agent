import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import logging

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_credentials():
    """Authorization — returns creds object"""
    creds = None
    if os.path.exists("token.json"):
        logger.info("Loading credentials from token.json...")
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Token expired, refreshing...")
            creds.refresh(Request())
        else:
            logger.info("No valid token found, starting OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token_file:
            token_file.write(creds.to_json())
        logger.info("Credentials saved to token.json.")
    return creds

def get_hyperlinks(spreadsheet_id, tab_name, creds):
    """Fetches hyperlinks from column A for the given tab. Returns {row_index: url}"""
    logger.info(f"Fetching hyperlinks from tab: {tab_name}...")
    service = build('sheets', 'v4', credentials=creds)
    result = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        ranges=[f"{tab_name}!A:A"],
        includeGridData=True
    ).execute()

    links = {}
    rows = result['sheets'][0]['data'][0].get('rowData', [])
    for i, row in enumerate(rows):
        values = row.get('values', [{}])
        if values:
            hyperlink = values[0].get('hyperlink', None)
            if hyperlink:
                links[i] = hyperlink

    logger.info(f"Found {len(links)} hyperlinks in tab: {tab_name}.")
    return links

def get_all_rows(spreadsheet_id):
    """Reads both tabs (2025, 2026). Each row is a dict with data + crm_link field."""
    logger.info("Connecting to Google Sheets...")
    creds = get_credentials()
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)

    all_rows = {}

    for tab_name in ["2025", "2026"]:
        logger.info(f"Reading tab: {tab_name}...")
        try:
            worksheet = spreadsheet.worksheet(tab_name)
            rows = worksheet.get_all_records()
            links = get_hyperlinks(spreadsheet_id, tab_name, creds)

            for i, row in enumerate(rows):
                row["crm_link"] = links.get(i + 1, None)

            all_rows[tab_name] = rows
            logger.info(f"Tab {tab_name}: loaded {len(rows)} rows.")
        except Exception as e:
            logger.error(f"Failed to read tab {tab_name}: {e}")

    return all_rows

def update_status(spreadsheet_id, tab_name, row_index, new_status):
    logger.info(f"Updating status in tab {tab_name}, row {row_index + 2} → '{new_status}'")
    try:
        creds = get_credentials()
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(tab_name)
        cell = f"C{row_index + 2}"
        worksheet.update(cell, [[new_status]])
        logger.info(f"Status updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update status: {e}")
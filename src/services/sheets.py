"""Google Sheets API integration."""

import logging
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SheetsService:
    """Service for interacting with Google Sheets API."""

    def __init__(self):
        self._service = None

    def connect(self) -> bool:
        """Establish connection to Google Sheets API."""
        if settings.demo_mode:
            logger.info("Demo mode: Simulating Google Sheets connection")
            return True

        try:
            creds = Credentials.from_service_account_file(
                settings.google_credentials_file,
                scopes=SCOPES,
            )
            self._service = build("sheets", "v4", credentials=creds)
            logger.info("Connected to Google Sheets API successfully")
            return True
        except FileNotFoundError:
            logger.error(f"Credentials file not found: {settings.google_credentials_file}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            return False

    def read_sheet(self, range_name: str = "A:Z") -> list[list[Any]]:
        """Read data from the configured spreadsheet."""
        if settings.demo_mode:
            logger.info("Demo mode: Returning empty sheet data")
            return []

        if not self._service:
            raise RuntimeError("Not connected to Sheets. Call connect() first.")

        try:
            sheet = self._service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=settings.google_spreadsheet_id,
                range=f"{settings.google_sheet_name}!{range_name}",
            ).execute()

            values = result.get("values", [])
            logger.info(f"Read {len(values)} rows from sheet")
            return values
        except HttpError as e:
            logger.error(f"Failed to read sheet: {e}")
            raise

    def write_sheet(self, data: list[list[Any]], start_cell: str = "A1") -> int:
        """Write data to the configured spreadsheet."""
        if settings.demo_mode:
            logger.info(f"Demo mode: Would write {len(data)} rows to sheet")
            return len(data)

        if not self._service:
            raise RuntimeError("Not connected to Sheets. Call connect() first.")

        try:
            sheet = self._service.spreadsheets()

            # Clear existing data first
            sheet.values().clear(
                spreadsheetId=settings.google_spreadsheet_id,
                range=f"{settings.google_sheet_name}!A:Z",
            ).execute()

            # Write new data
            result = sheet.values().update(
                spreadsheetId=settings.google_spreadsheet_id,
                range=f"{settings.google_sheet_name}!{start_cell}",
                valueInputOption="USER_ENTERED",
                body={"values": data},
            ).execute()

            updated_rows = result.get("updatedRows", 0)
            logger.info(f"Wrote {updated_rows} rows to sheet")
            return updated_rows
        except HttpError as e:
            logger.error(f"Failed to write to sheet: {e}")
            raise

    def append_row(self, row: list[Any]) -> bool:
        """Append a single row to the sheet."""
        if settings.demo_mode:
            logger.info(f"Demo mode: Would append row: {row}")
            return True

        if not self._service:
            raise RuntimeError("Not connected to Sheets. Call connect() first.")

        try:
            sheet = self._service.spreadsheets()
            sheet.values().append(
                spreadsheetId=settings.google_spreadsheet_id,
                range=f"{settings.google_sheet_name}!A:A",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": [row]},
            ).execute()
            return True
        except HttpError as e:
            logger.error(f"Failed to append row: {e}")
            return False


# Singleton instance
sheets_service = SheetsService()

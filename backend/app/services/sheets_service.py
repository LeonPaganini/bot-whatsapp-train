import logging
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from app.core.config import settings

LOGGER = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SheetsService:
    def __init__(self) -> None:
        if not settings.google_sheet_id:
            raise RuntimeError("GOOGLE_SHEET_ID is required")
        if not settings.service_account_info:
            raise RuntimeError("Service account credentials not provided")
        credentials = Credentials.from_service_account_info(
            settings.service_account_info, scopes=SCOPES
        )
        self.sheet_id = settings.google_sheet_id
        self.service = build("sheets", "v4", credentials=credentials)

    def get_values(self, sheet_name: str) -> list[list[str]]:
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self.sheet_id, range=sheet_name)
            .execute()
        )
        return result.get("values", [])

    def append_rows(self, sheet_name: str, rows: list[list[Any]]) -> None:
        if not rows:
            return
        body = {"values": rows}
        (
            self.service.spreadsheets()
            .values()
            .append(
                spreadsheetId=self.sheet_id,
                range=sheet_name,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )

    def update_row(self, sheet_name: str, row_index: int, row_values: list[Any]) -> None:
        if row_index < 1:
            raise ValueError("row_index must be >= 1")
        end_col = chr(ord("A") + len(row_values) - 1)
        range_name = f"{sheet_name}!A{row_index}:{end_col}{row_index}"
        body = {"values": [row_values]}
        (
            self.service.spreadsheets()
            .values()
            .update(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )

    def ensure_sheet(self, sheet_name: str, headers: list[str]) -> None:
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
        sheets = [sheet["properties"]["title"] for sheet in spreadsheet.get("sheets", [])]
        if sheet_name not in sheets:
            LOGGER.info("Creating sheet %s", sheet_name)
            body = {"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id, body=body
            ).execute()
            self.append_rows(sheet_name, [headers])
            return

        values = self.get_values(sheet_name)
        if not values:
            self.append_rows(sheet_name, [headers])

    def find_row_by_value(
        self, sheet_name: str, column_index: int, value: str
    ) -> tuple[int | None, list[str] | None]:
        values = self.get_values(sheet_name)
        if not values:
            return None, None
        for idx, row in enumerate(values[1:], start=2):
            if len(row) > column_index and row[column_index] == value:
                return idx, row
        return None, None

    def replace_rows(self, sheet_name: str, rows: list[list[Any]]) -> None:
        body = {"values": rows}
        self.service.spreadsheets().values().clear(
            spreadsheetId=self.sheet_id, range=sheet_name, body={}
        ).execute()
        self.service.spreadsheets().values().update(
            spreadsheetId=self.sheet_id,
            range=sheet_name,
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()

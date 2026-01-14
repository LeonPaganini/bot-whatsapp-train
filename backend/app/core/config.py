import json
import os
from dataclasses import dataclass


def _load_service_account() -> dict | None:
    raw_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw_json:
        return json.loads(raw_json)
    file_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if file_path and os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return None


@dataclass(frozen=True)
class Settings:
    env: str
    google_sheet_id: str
    service_account_info: dict | None
    whatsapp_token: str | None
    whatsapp_phone_number_id: str | None
    whatsapp_verify_token: str | None
    base_url: str | None


settings = Settings(
    env=os.getenv("ENV", "dev"),
    google_sheet_id=os.getenv("GOOGLE_SHEET_ID", ""),
    service_account_info=_load_service_account(),
    whatsapp_token=os.getenv("WHATSAPP_TOKEN"),
    whatsapp_phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID"),
    whatsapp_verify_token=os.getenv("WHATSAPP_VERIFY_TOKEN"),
    base_url=os.getenv("BASE_URL"),
)

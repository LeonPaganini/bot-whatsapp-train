import datetime as dt
import hashlib
import re
from typing import Iterable


def now_iso() -> str:
    return dt.datetime.utcnow().isoformat()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[\s-]+", "-", value)
    return value.strip("-")


def short_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:6]


def normalize_whatsapp(value: str) -> str:
    value = value.strip()
    if not value.startswith("+"):
        value = "+" + re.sub(r"\D", "", value)
    return value


def parse_loads(value: str) -> list[float]:
    cleaned = re.sub(r"[\s,]+", "/", value.strip())
    parts = [part for part in cleaned.split("/") if part]
    loads: list[float] = []
    for part in parts:
        try:
            loads.append(float(part))
        except ValueError:
            continue
    return loads


def monday_start(date_str: str) -> str:
    date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    monday = date - dt.timedelta(days=date.weekday())
    return monday.isoformat()


def year_month(date_str: str) -> str:
    date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    return f"{date.year:04d}-{date.month:02d}"


def first_non_empty(values: Iterable[str | None]) -> str | None:
    for value in values:
        if value:
            return value
    return None

"""Flight row validation and airport lookup module."""

from datetime import datetime
import math
import re

_CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{2,8}$")
_IATA_PATTERN = re.compile(r"^[A-Z]{3}$")
_STAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
_TIME_FMT = "%Y-%m-%d %H:%M"

_OUTPUT_KEYS = (
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price",
)


def load_airports(path: str) -> set[str]:
    """Load valid airport codes from a text file."""
    valid_codes: set[str] = set()
    with open(path, encoding="utf-8") as stream:
        for raw in stream:
            entry = raw.strip()
            if entry and not entry.startswith("#"):
                valid_codes.add(entry)
    return valid_codes


def _as_timestamp(raw_stamp: str) -> datetime | None:
    if not _STAMP_PATTERN.match(raw_stamp):
        return None
    try:
        return datetime.strptime(raw_stamp, _TIME_FMT)
    except ValueError:
        return None


def _as_positive_amount(raw_amount: str) -> tuple[bool, float | None]:
    try:
        number = float(raw_amount)
    except ValueError:
        return False, None
    if not math.isfinite(number):
        return False, None
    if number <= 0:
        return True, None
    return True, number


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Validate a single CSV row and return the first error code or None."""
    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"

    cleaned = [item.strip() for item in fields]
    if any(not item for item in cleaned):
        return "MISSING_FIELD"

    flight_code, dep_code, arr_code, dep_raw, arr_raw, fare_raw = cleaned

    if not _CODE_PATTERN.match(flight_code):
        return "INVALID_FLIGHT_ID"

    if not (_IATA_PATTERN.match(dep_code) and dep_code in airports):
        return "INVALID_ORIGIN"

    if not (_IATA_PATTERN.match(arr_code) and arr_code in airports):
        return "INVALID_DESTINATION"

    if dep_code == arr_code:
        return "SAME_ORIGIN_DESTINATION"

    dep_dt = _as_timestamp(dep_raw)
    if dep_dt is None:
        return "INVALID_DEPARTURE"

    arr_dt = _as_timestamp(arr_raw)
    if arr_dt is None:
        return "INVALID_ARRIVAL"

    if arr_dt <= dep_dt:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    finite_ok, positive_fare = _as_positive_amount(fare_raw)
    if not finite_ok:
        return "INVALID_PRICE"

    if positive_fare is None:
        return "NON_POSITIVE_PRICE"

    return None


def to_record(fields: list[str]) -> dict:
    """Build a normalized flight record dictionary from valid row fields."""
    cleaned = [item.strip() for item in fields]
    record = {key: val for key, val in zip(_OUTPUT_KEYS, cleaned)}
    record["price"] = float(record["price"])
    return record
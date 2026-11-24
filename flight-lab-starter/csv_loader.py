"""Read flight CSV files, validate rows, and track duplicates"""
import csv
from pathlib import Path

from validator import to_record, validate_row


def _split_csv_lines(file_path: str) -> list[str]:
    raw_text = Path(file_path).read_text(encoding="utf-8")
    raw_lines = raw_text.splitlines()
    return raw_lines


def _skip_line(line: str) -> bool:
    trimmed = line.strip()
    return len(trimmed) == 0 or trimmed.startswith("#")


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    valid_flights: list[dict] = []
    error_lines: list[str] = []
    seen_pairs: set[tuple[str, str]] = set()

    for csv_path in paths:
        fname = Path(csv_path).name
        all_lines = _split_csv_lines(csv_path)

        for line_no in range(2, len(all_lines) + 1):
            current = all_lines[line_no - 1]
            if _skip_line(current):
                continue

            parsed = next(csv.reader([current]), [])
            code = validate_row(parsed, airports)

            if code is not None:
                error_lines.append(f"{fname}:{line_no}: {code} | {current}")
                continue

            flight_obj = to_record(parsed)
            pair = (flight_obj["flight_id"], flight_obj["departure_datetime"])

            if pair in seen_pairs:
                error_lines.append(f"{fname}:{line_no}: DUPLICATE_FLIGHT | {current}")
                continue

            seen_pairs.add(pair)
            valid_flights.append(flight_obj)

    return valid_flights, error_lines
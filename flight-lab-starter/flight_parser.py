"""CLI entry point for parsing flight schedules and running queries."""
import argparse
from datetime import datetime
import json
import logging
from pathlib import Path
import sys

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

STUDENT_ID = "251ADB072"
FIRST_NAME = "Naim"
LAST_NAME = "Khuduzade"

LOGGER_NAME = "flight_parser"


class AppError(Exception):
    pass


def _create_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Validate flight CSV data and run queries.")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("-i", metavar="FILE", help="single CSV input file")
    group.add_argument("-d", metavar="FOLDER", help="folder containing CSV files")
    group.add_argument("-j", metavar="FILE", help="existing JSON flight database")
    p.add_argument("-a", metavar="FILE", help="airport codes file")
    p.add_argument("-o", metavar="FILE", help="output JSON path (default: db.json)")
    p.add_argument("-q", metavar="FILE", help="queries JSON file")
    p.add_argument("-r", metavar="FOLDER", default=".", help="output folder for response JSON")
    return p


def _read_json(filepath: str):
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except OSError as err:
        raise AppError(f"cannot read {filepath}: {err.strerror}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise AppError(f"{filepath} is not valid JSON")


def _write_json(filepath: str, content) -> None:
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
    except OSError as err:
        raise AppError(f"cannot write {filepath}: {err.strerror}")


def _collect_csvs(opts) -> list[str]:
    if opts.i:
        target = Path(opts.i)
        if not target.is_file():
            raise AppError(f"file not found: {opts.i}")
        return [str(target)]

    folder = Path(opts.d)
    if not folder.is_dir():
        raise AppError(f"folder not found: {opts.d}")

    csv_files = sorted(
        entry.name
        for entry in folder.iterdir()
        if entry.is_file() and entry.name.endswith(".csv")
    )
    if not csv_files:
        raise AppError(f"no .csv files in {opts.d}")

    return [str(folder / name) for name in csv_files]


def _save_error_log(log_file: str, warnings: list[str]) -> None:
    log = logging.getLogger(LOGGER_NAME)
    log.setLevel(logging.INFO)
    fh = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    fh.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    log.addHandler(fh)
    try:
        for msg in warnings:
            log.warning(msg)
    finally:
        log.removeHandler(fh)
        fh.close()


def _run_pipeline(opts) -> int:
    if opts.j:
        flights = _read_json(opts.j)
        if not isinstance(flights, list) or not all(isinstance(item, dict) for item in flights):
            raise AppError(f"{opts.j} must be a JSON array of objects")
    else:
        csv_list = _collect_csvs(opts)
        try:
            airports = load_airports(opts.a)
        except OSError as err:
            raise AppError(f"cannot read airport file {opts.a}: {err.strerror}")
        except UnicodeDecodeError:
            raise AppError(f"cannot read airport file {opts.a}")

        try:
            flights, warnings = parse_files(csv_list, airports)
        except OSError as err:
            raise AppError(f"cannot read CSV file: {err.strerror}")
        except UnicodeDecodeError:
            raise AppError("CSV file is not valid UTF-8")

        db_out = opts.o or "db.json"
        _write_json(db_out, flights)

        log_out = str(Path(db_out).resolve().parent / "errors.log")
        try:
            _save_error_log(log_out, warnings)
        except OSError as err:
            raise AppError(f"cannot write {log_out}: {err.strerror}")

        print(f"{len(flights)} valid flights, {len(warnings)} invalid rows")

    if opts.q:
        raw_queries = _read_json(opts.q)
        if not isinstance(raw_queries, (dict, list)):
            raise AppError(f"{opts.q} must be a query object or list of query objects")
        if isinstance(raw_queries, list) and not all(isinstance(q, dict) for q in raw_queries):
            raise AppError(f"{opts.q} must contain only query objects")

        out_items = run_queries(flights, raw_queries)
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        resp_name = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{stamp}.json"
        _write_json(str(Path(opts.r) / resp_name), out_items)
        print(f"{len(out_items)} queries answered, saved to {resp_name}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _create_arg_parser()
    try:
        opts = parser.parse_args(argv)
        if (opts.i or opts.d) and not opts.a:
            parser.error("-a is required with -i or -d")
        if opts.j and opts.o:
            parser.error("-o cannot be used with -j")
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2

    try:
        return _run_pipeline(opts)
    except AppError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
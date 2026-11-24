"""Filter, sort, and limit flight records from queries."""
from datetime import datetime

RECORD_KEYS = {
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price",
}
QUERY_KEYS = RECORD_KEYS | {"min_price", "sort_by", "order", "limit"}
DT_FMT = "%Y-%m-%d %H:%M"


def _is_number(val) -> bool:
    # Python treats bool as a subclass of int, so exclude booleans explicitly
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def _valid_dt(text) -> bool:
    if not isinstance(text, str) or len(text) != 16 or text[10] != " ":
        return False
    try:
        datetime.strptime(text, DT_FMT)
        return True
    except ValueError:
        return False


def _valid_query(q) -> bool:
    if not isinstance(q, dict):
        return False

    for k in q:
        if k not in QUERY_KEYS:
            return False

    if "order" in q and "sort_by" not in q:
        return False

    for k in ("flight_id", "origin", "destination"):
        if k in q and not isinstance(q[k], str):
            return False

    for k in ("departure_datetime", "arrival_datetime"):
        if k in q and not _valid_dt(q[k]):
            return False

    for k in ("price", "min_price"):
        if k in q and not _is_number(q[k]):
            return False

    if "sort_by" in q:
        if not isinstance(q["sort_by"], str) or q["sort_by"] not in RECORD_KEYS:
            return False

    if "order" in q and q["order"] not in ("asc", "desc"):
        return False

    if "limit" in q:
        lim = q["limit"]
        if isinstance(lim, bool) or not isinstance(lim, int) or lim < 0:
            return False

    return True


def _matches_query(flight: dict, q: dict) -> bool:
    if "flight_id" in q and flight["flight_id"] != q["flight_id"]:
        return False
    if "origin" in q and flight["origin"] != q["origin"]:
        return False
    if "destination" in q and flight["destination"] != q["destination"]:
        return False
    if "departure_datetime" in q and flight["departure_datetime"] < q["departure_datetime"]:
        return False
    if "arrival_datetime" in q and flight["arrival_datetime"] > q["arrival_datetime"]:
        return False
    if "price" in q and flight["price"] > q["price"]:
        return False
    if "min_price" in q and flight["price"] < q["min_price"]:
        return False
    return True


def run_query(db: list[dict], query: dict) -> dict:
    if not _valid_query(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}

    rows = [f for f in db if _matches_query(f, query)]

    if "sort_by" in query:
        field = query["sort_by"]
        rev = query.get("order", "asc") == "desc"
        rows = sorted(rows, key=lambda f: f[field], reverse=rev)

    if "limit" in query:
        rows = rows[: query["limit"]]

    return {"query": query, "matches": rows}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    query_list = [queries] if isinstance(queries, dict) else list(queries)
    return [run_query(db, q) for q in query_list]
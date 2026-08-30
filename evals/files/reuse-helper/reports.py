# Reporting helpers. Amount strings in CSV rows look like "$12.50".
# Summation belongs here; parsing already lives in billing.py.


def row_count(rows: list[dict[str, str]]) -> int:
    return len(rows)

"""Compare liquid reserves and scheduled unlocks against dated obligations with earliest shortfall detection."""

from .common import (
    number,
    integer,
    identity,
    records,
    chronology,
    allocate,
    result,
    validate_document,
)
from decimal import Decimal


def _analyze(d):
    cash = integer(d["liquid"])
    inflows = records(d["inflows"], "id")
    outflows = records(d["obligations"], "id")
    calendar = {}
    for direction, rows in ((1, inflows), (-1, outflows)):
        for r in rows:
            t = integer(r["timestamp"])
            amount = integer(r["amount"])
            entry = calendar.setdefault(t, {"inflow": 0, "outflow": 0})
            entry["inflow" if direction == 1 else "outflow"] += amount
    trace = []
    shortfall = None
    minimum = cash
    for t, e in sorted(calendar.items()):
        cash += e["inflow"] - e["outflow"]
        minimum = min(minimum, cash)
        if cash < 0 and shortfall is None:
            shortfall = t
        trace.append({"timestamp": t, **e, "balance": cash, "shortfall": max(-cash, 0)})
    return {
        "timeline": trace,
        "first_shortfall": shortfall,
        "funding_required": max(-minimum, 0),
        "ending_balance": cash,
    }


def analyze(document):
    validate_document(document)
    try:
        return result(_analyze(document))
    except (KeyError, TypeError, ArithmeticError, RecursionError) as error:
        raise ValueError("invalid domain input: " + str(error)) from error

"""Deterministic screening tools. Missing data never establishes absence."""

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import calendar


def calendar_months_before(day: date, months: int) -> date:
    if type(months) is not int or not 0 <= months <= 1200:
        raise ValueError("invalid month window")
    index = day.year * 12 + day.month - 1 - months
    year, month = divmod(index, 12)
    month += 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def numerical(value: str | None, operator: str, threshold: str,
              unit: str, expected_unit: str) -> str:
    if value is None or unit != expected_unit:
        return "unknown"
    try:
        left, right = Decimal(value), Decimal(threshold)
        if not left.is_finite() or not right.is_finite():
            return "unknown"
        comparisons = {"gt": left > right, "gte": left >= right,
                       "lt": left < right, "lte": left <= right, "eq": left == right}
        return "supported" if comparisons[operator] else "contradicted"
    except (InvalidOperation, KeyError, TypeError, ValueError):
        return "unknown"


def temporal(events: list[str], as_of: str, months: int,
             complete_since: str | None = None,
             complete_through: str | None = None) -> str:
    """Inclusive calendar window; negative evidence needs full window coverage."""
    try:
        end = date.fromisoformat(as_of)
        start = calendar_months_before(end, months)
        dates = [date.fromisoformat(event) for event in events]
        if any(start <= event <= end for event in dates):
            return "supported"
        if (complete_since and complete_through
                and date.fromisoformat(complete_since) <= start
                and date.fromisoformat(complete_through) >= end):
            return "contradicted"
    except (ValueError, TypeError, OverflowError):
        pass
    return "unknown"


def temporal_days(events, as_of, days, complete_since=None, complete_through=None):
    """Inclusive elapsed-day window, distinct from calendar-month arithmetic."""
    try:
        if type(days) is not int or not 0 <= days <= 36600:
            return 'unknown'
        end = date.fromisoformat(as_of)
        start = end - timedelta(days=days)
        dates = [date.fromisoformat(event) for event in events]
        if any(start <= event <= end for event in dates):
            return 'supported'
        if (complete_since and complete_through and
                date.fromisoformat(complete_since) <= start and
                date.fromisoformat(complete_through) >= end):
            return 'contradicted'
    except (ValueError, TypeError, OverflowError):
        pass
    return 'unknown'

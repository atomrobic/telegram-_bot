"""General helper utilities."""

from __future__ import annotations

import calendar
from datetime import date

from telegram import User


def get_display_name(user: User) -> str:
    """Generate a friendly name from Telegram user fields."""
    full_name = " ".join(part for part in [user.first_name, user.last_name] if part).strip()
    if full_name:
        return full_name
    if user.username:
        return user.username
    return f"Employee {user.id}"


def get_month_range(target_date: date) -> tuple[date, date]:
    """Return the first and last calendar day for the month."""
    last_day = calendar.monthrange(target_date.year, target_date.month)[1]
    return date(target_date.year, target_date.month, 1), date(target_date.year, target_date.month, last_day)


def format_leave_balance(total_allowed: int, used: int, remaining: int) -> str:
    """Create a readable leave balance message."""
    return (
        "Leave Balance\n"
        f"Total leaves allowed: {total_allowed}\n"
        f"Leaves used: {used}\n"
        f"Remaining leaves: {remaining}"
    )

"""SQLite database access layer."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Employee:
    """Database model for an employee."""

    id: int
    name: str
    telegram_id: int


@dataclass(frozen=True)
class LeaveBalance:
    """Current-month leave usage summary."""

    total_allowed: int
    used: int
    remaining: int


@contextmanager
def get_connection(database_path: str):
    """Provide a SQLite connection with row access by column name."""
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db(database_path: str) -> None:
    """Create required tables if they do not already exist."""
    with get_connection(database_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                telegram_id INTEGER NOT NULL UNIQUE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Present', 'Leave')),
                UNIQUE(employee_id, date),
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            )
            """
        )


def upsert_employee(database_path: str, telegram_id: int, name: str) -> Employee:
    """Register a new employee or refresh the stored name for an existing one."""
    with get_connection(database_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO employees (name, telegram_id)
            VALUES (?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET name = excluded.name
            """,
            (name, telegram_id),
        )
        cursor.execute(
            "SELECT id, name, telegram_id FROM employees WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = cursor.fetchone()
        return Employee(id=row["id"], name=row["name"], telegram_id=row["telegram_id"])


def get_employee_by_telegram_id(database_path: str, telegram_id: int) -> Employee | None:
    """Fetch a single employee by Telegram user ID."""
    with get_connection(database_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, name, telegram_id FROM employees WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Employee(id=row["id"], name=row["name"], telegram_id=row["telegram_id"])


def list_employees(database_path: str) -> list[Employee]:
    """List employees ordered by name."""
    with get_connection(database_path) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name, telegram_id FROM employees ORDER BY name ASC")
        rows = cursor.fetchall()
        return [Employee(id=row["id"], name=row["name"], telegram_id=row["telegram_id"]) for row in rows]


def record_attendance(
    database_path: str, employee_id: int, attendance_date: date, status: str
) -> bool:
    """Insert a daily attendance record. Returns False on duplicate submission."""
    with get_connection(database_path) as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO attendance (employee_id, date, status)
                VALUES (?, ?, ?)
                """,
                (employee_id, attendance_date.isoformat(), status),
            )
        except sqlite3.IntegrityError:
            return False
        return True


def count_used_leaves(
    database_path: str, employee_id: int, month_start: date, month_end: date
) -> int:
    """Count leave records for an employee in the given month."""
    with get_connection(database_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) AS leave_count
            FROM attendance
            WHERE employee_id = ?
              AND status = 'Leave'
              AND date BETWEEN ? AND ?
            """,
            (employee_id, month_start.isoformat(), month_end.isoformat()),
        )
        row = cursor.fetchone()
        return int(row["leave_count"])


def get_leave_balance(
    database_path: str, employee_id: int, month_start: date, month_end: date, monthly_limit: int
) -> LeaveBalance:
    """Calculate the monthly leave balance for an employee."""
    used = count_used_leaves(database_path, employee_id, month_start, month_end)
    remaining = max(monthly_limit - used, 0)
    return LeaveBalance(total_allowed=monthly_limit, used=used, remaining=remaining)


def get_attendance_for_date(database_path: str, attendance_date: date) -> list[sqlite3.Row]:
    """Fetch all attendance rows for a specific day."""
    with get_connection(database_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT e.name, e.telegram_id, a.status
            FROM attendance a
            JOIN employees e ON e.id = a.employee_id
            WHERE a.date = ?
            ORDER BY e.name ASC
            """,
            (attendance_date.isoformat(),),
        )
        return cursor.fetchall()


def get_monthly_summary(database_path: str, month_start: date, month_end: date) -> list[sqlite3.Row]:
    """Return a monthly present/leave summary for every employee."""
    with get_connection(database_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                e.id AS employee_id,
                e.name AS name,
                e.telegram_id AS telegram_id,
                COALESCE(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END), 0) AS presents,
                COALESCE(SUM(CASE WHEN a.status = 'Leave' THEN 1 ELSE 0 END), 0) AS leaves
            FROM employees e
            LEFT JOIN attendance a
                ON a.employee_id = e.id
               AND a.date BETWEEN ? AND ?
            GROUP BY e.id, e.name, e.telegram_id
            ORDER BY e.name ASC
            """,
            (month_start.isoformat(), month_end.isoformat()),
        )
        return cursor.fetchall()

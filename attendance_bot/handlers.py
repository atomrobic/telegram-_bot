"""Telegram command and callback handlers."""

from __future__ import annotations

import logging
from datetime import date

from telegram import Update
from telegram.ext import CallbackContext

from attendance_bot.config import Settings
from attendance_bot.db import (
    Employee,
    get_attendance_for_date,
    get_employee_by_telegram_id,
    get_leave_balance,
    get_monthly_summary,
    list_employees,
    record_attendance,
    upsert_employee,
)
from attendance_bot.keyboards import main_menu_keyboard
from attendance_bot.utils import format_leave_balance, get_display_name, get_month_range

LOGGER = logging.getLogger(__name__)


class BotHandlers:
    """Collection of Telegram bot handlers with shared configuration."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _register_employee(self, update: Update) -> Employee:
        """Ensure the Telegram user exists in the employees table."""
        user = update.effective_user
        employee_name = get_display_name(user)
        return upsert_employee(self.settings.database_path, user.id, employee_name)

    def _get_or_register_employee(self, update: Update) -> Employee:
        """Load an employee or register them automatically."""
        employee = get_employee_by_telegram_id(self.settings.database_path, update.effective_user.id)
        if employee is None:
            employee = self._register_employee(update)
        return employee

    def _is_admin(self, telegram_id: int) -> bool:
        """Check whether the current user is allowed to use admin commands."""
        return telegram_id in self.settings.admin_telegram_ids

    async def start(self, update: Update, context: CallbackContext) -> None:
        """Register the employee and show the main action buttons."""
        employee = self._register_employee(update)
        await update.message.reply_text(
            (
                f"Hi {employee.name}, your attendance bot is ready.\n\n"
                "Use the buttons below to mark attendance, apply leave, or check your leave balance."
            ),
            reply_markup=main_menu_keyboard(),
        )

    async def button_handler(self, update: Update, context: CallbackContext) -> None:
        """Handle inline button actions for employee operations."""
        query = update.callback_query
        await query.answer()

        employee = self._get_or_register_employee(update)
        today = date.today()
        month_start, month_end = get_month_range(today)

        if query.data == "mark_present":
            created = record_attendance(self.settings.database_path, employee.id, today, "Present")
            if created:
                message = f"Attendance marked as Present for {today.isoformat()}."
            else:
                message = f"You have already submitted attendance for {today.isoformat()}."
            await query.edit_message_text(message, reply_markup=main_menu_keyboard())
            return

        if query.data == "mark_leave":
            balance = get_leave_balance(
                self.settings.database_path,
                employee.id,
                month_start,
                month_end,
                self.settings.monthly_leave_limit,
            )
            if balance.remaining <= 0:
                await query.edit_message_text(
                    "You have no leave balance left for this month.",
                    reply_markup=main_menu_keyboard(),
                )
                return

            created = record_attendance(self.settings.database_path, employee.id, today, "Leave")
            if created:
                updated_balance = get_leave_balance(
                    self.settings.database_path,
                    employee.id,
                    month_start,
                    month_end,
                    self.settings.monthly_leave_limit,
                )
                message = (
                    f"Leave marked for {today.isoformat()}.\n"
                    f"Remaining leaves this month: {updated_balance.remaining}"
                )
            else:
                message = f"You have already submitted attendance for {today.isoformat()}."
            await query.edit_message_text(message, reply_markup=main_menu_keyboard())
            return

        if query.data == "my_balance":
            balance = get_leave_balance(
                self.settings.database_path,
                employee.id,
                month_start,
                month_end,
                self.settings.monthly_leave_limit,
            )
            await query.edit_message_text(
                format_leave_balance(balance.total_allowed, balance.used, balance.remaining),
                reply_markup=main_menu_keyboard(),
            )
            return

        LOGGER.warning("Unhandled callback data received: %s", query.data)
        await query.edit_message_text("Unknown action.", reply_markup=main_menu_keyboard())

    async def report(self, update: Update, context: CallbackContext) -> None:
        """Show today's attendance summary to admins."""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("You are not allowed to use this command.")
            return

        today = date.today()
        rows = get_attendance_for_date(self.settings.database_path, today)
        if not rows:
            await update.message.reply_text(f"No attendance records found for {today.isoformat()}.")
            return

        present_names = [row["name"] for row in rows if row["status"] == "Present"]
        leave_names = [row["name"] for row in rows if row["status"] == "Leave"]

        message = (
            f"Attendance Report for {today.isoformat()}\n"
            f"Present: {len(present_names)}\n"
            f"Leave: {len(leave_names)}\n\n"
            f"Present Employees: {', '.join(present_names) if present_names else 'None'}\n"
            f"On Leave: {', '.join(leave_names) if leave_names else 'None'}"
        )
        await update.message.reply_text(message)

    async def monthly(self, update: Update, context: CallbackContext) -> None:
        """Show a month-to-date summary for all employees."""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("You are not allowed to use this command.")
            return

        today = date.today()
        month_start, month_end = get_month_range(today)
        rows = get_monthly_summary(self.settings.database_path, month_start, month_end)
        if not rows:
            await update.message.reply_text("No employees are registered yet.")
            return

        lines = [f"Monthly Summary ({month_start.isoformat()} to {today.isoformat()})"]
        for row in rows:
            remaining = max(self.settings.monthly_leave_limit - int(row["leaves"]), 0)
            lines.append(
                f"{row['name']}: Present {row['presents']}, Leave {row['leaves']}, Remaining Leave {remaining}"
            )
        await update.message.reply_text("\n".join(lines))

    async def employees(self, update: Update, context: CallbackContext) -> None:
        """List all employees with their current leave balances."""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("You are not allowed to use this command.")
            return

        employees = list_employees(self.settings.database_path)
        if not employees:
            await update.message.reply_text("No employees are registered yet.")
            return

        today = date.today()
        month_start, month_end = get_month_range(today)
        lines = ["Registered Employees"]
        for employee in employees:
            balance = get_leave_balance(
                self.settings.database_path,
                employee.id,
                month_start,
                month_end,
                self.settings.monthly_leave_limit,
            )
            lines.append(
                f"{employee.name} (Telegram ID: {employee.telegram_id}) - Used {balance.used}, Remaining {balance.remaining}"
            )
        await update.message.reply_text("\n".join(lines))

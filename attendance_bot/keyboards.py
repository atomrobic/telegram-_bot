"""Telegram inline keyboard builders."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build the primary employee actions keyboard."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Present", callback_data="mark_present"),
                InlineKeyboardButton("Leave", callback_data="mark_leave"),
            ],
            [InlineKeyboardButton("My Balance", callback_data="my_balance")],
        ]
    )

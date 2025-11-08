"""Заглушка для настроек."""

from telegram import Update
from telegram.ext import ContextTypes

from src import keyboards


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает заглушку настроек."""
    await update.message.reply_text(
        "Настройки скоро появятся. Следите за обновлениями!",
        reply_markup=keyboards.main_menu_keyboard(),
    )

"""Хэндлер команды /start и приветствия."""

from telegram import Update
from telegram.ext import ContextTypes

from src import keyboards


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветствие и главное меню."""
    user_first_name = update.effective_user.first_name if update.effective_user else ""
    greeting = (
        "Привет! Я EventPilot — помогу зафиксировать события и вести проекты.\n"
        "Выберите действие из меню ниже."
    )
    if user_first_name:
        greeting = f"Привет, {user_first_name}!\n" + greeting
    await update.message.reply_text(greeting, reply_markup=keyboards.main_menu_keyboard())
    context.user_data.clear()

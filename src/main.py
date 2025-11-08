"""Точка входа Telegram-бота EventPilot."""

from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.handlers import new_event, projects, settings, start, stats
from src.states import (
    STATE_NEW_EVENT_DESCRIPTION,
    STATE_PROJECT_CONFIRM,
    STATE_PROJECT_EDIT,
    STATE_PROJECT_SELECT,
)

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Главный обработчик текстовых сообщений."""
    if not update.message:
        return
    text = (update.message.text or "").strip()
    state = context.user_data.get("state")

    if text == "🔙 Главное меню":
        context.user_data.clear()
        await start.start(update, context)
        return

    if state == STATE_NEW_EVENT_DESCRIPTION:
        await new_event.handle_description(update, context)
        return

    if state == STATE_PROJECT_SELECT:
        await projects.select_project(update, context)
        return

    if state == STATE_PROJECT_EDIT:
        if text in {"✅ Да", "⛔️ Отмена"}:
            # Пользователь в режиме редактирования, но кнопки подтверждения неактуальны
            await update.message.reply_text(
                "Сначала сформулируйте изменение или вернитесь в меню.",
            )
            return
        await projects.process_edit(update, context)
        return

    if state == STATE_PROJECT_CONFIRM:
        await projects.confirm_change(update, context)
        return

    if text == "Новое событие":
        await new_event.ask_description(update, context)
        return

    if text == "Мои проекты":
        await projects.show_projects(update, context)
        return

    if text == "Статистика":
        await stats.show_stats(update, context)
        return

    if text == "Настройки":
        await settings.show_settings(update, context)
        return

    await update.message.reply_text(
        "Я пока не понимаю этот запрос. Пожалуйста, воспользуйтесь меню.",
    )


def build_application(token: str) -> Application:
    """Создаёт и настраивает приложение бота."""
    application = (
        ApplicationBuilder()
        .token(token)
        .build()
    )
    application.add_handler(CommandHandler("start", start.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return application


async def main() -> None:
    """Точка входа."""
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("Не найден TELEGRAM_TOKEN в окружении. Заполните .env файл.")

    application = build_application(token)
    LOGGER.info("Запускаем EventPilot")
    await application.initialize()
    await application.start()
    try:
        await application.updater.start_polling()
        await asyncio.Event().wait()
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

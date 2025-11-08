"""Логика сценария «Новое событие»."""

from telegram import Update
from telegram.ext import ContextTypes

from src import keyboards, nlp, storage
from src.states import STATE_NEW_EVENT_DESCRIPTION

PROMPT_TEXT = (
    "Опиши событие: дата, время, место, название, для кого, формат, бюджет (если есть).\n"
    "Можно в свободной форме."
)


async def ask_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Просит пользователя описать событие."""
    context.user_data["state"] = STATE_NEW_EVENT_DESCRIPTION
    await update.message.reply_text(PROMPT_TEXT, reply_markup=keyboards.main_menu_keyboard())


async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текст пользователя и сохраняет проект."""
    text = (update.message.text or "").strip()
    project = nlp.parse_freeform(text)
    storage.save_project(project)
    context.user_data.clear()

    sections = project.get("sections", {})
    section_names = ", ".join(name for name, data in sections.items() if data.get("notes"))
    if not section_names:
        section_names = ", ".join(sections.keys())
    summary = (
        f"Создано: {project.get('title')} — "
        f"{project.get('date') or 'дата не указана'} "
        f"{project.get('time') or ''} — {project.get('place') or 'место не указано'}.\n"
        f"Папки: {section_names}."
    )
    await update.message.reply_text(summary, reply_markup=keyboards.main_menu_keyboard())

"""Простая статистика по проектам."""

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from src import keyboards, storage


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет статистику по проектам."""
    summaries = storage.list_projects(limit=100)
    total = len(summaries)
    deadlines = []
    for summary in summaries:
        project = storage.load_project(summary.event_id)
        if not project:
            continue
        entries = project.get("sections", {}).get("дедлайны", {}).get("entries", [])
        for entry in entries:
            try:
                due_date = datetime.fromisoformat(entry.get("due_date"))
            except (TypeError, ValueError):
                continue
            deadlines.append(
                (
                    due_date,
                    project.get("title"),
                    entry.get("context"),
                )
            )
    deadlines.sort(key=lambda item: item[0])
    top_deadlines = deadlines[:3]
    if top_deadlines:
        deadline_lines = [
            f"— {item[0].date().isoformat()} — {item[1]} — {item[2]}" for item in top_deadlines
        ]
    else:
        deadline_lines = ["Ближайших дедлайнов нет."]

    message = (
        f"Всего проектов: {total}.\n" + "\n".join(deadline_lines)
    )
    await update.message.reply_text(message, reply_markup=keyboards.main_menu_keyboard())

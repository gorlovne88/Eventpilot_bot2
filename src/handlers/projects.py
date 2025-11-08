"""Работа с проектами."""

from __future__ import annotations

from typing import Dict, Optional

from telegram import Update
from telegram.ext import ContextTypes

from src import keyboards, nlp, storage
from src.states import (
    STATE_PROJECT_CONFIRM,
    STATE_PROJECT_EDIT,
    STATE_PROJECT_SELECT,
)


async def show_projects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает последние проекты."""
    summaries = storage.list_projects()
    if not summaries:
        await update.message.reply_text(
            "У вас пока нет проектов. Создайте новое событие!",
            reply_markup=keyboards.main_menu_keyboard(),
        )
        return

    titles_map: Dict[str, str] = {}
    pretty_list = []
    for summary in summaries:
        title = summary.title[:32]
        short_title = title
        if summary.date:
            short_title = f"{title} ({summary.date})"
        titles_map[short_title] = summary.event_id
        pretty_list.append(f"• {short_title}")

    context.user_data["state"] = STATE_PROJECT_SELECT
    context.user_data["project_map"] = titles_map
    await update.message.reply_text(
        "Последние проекты:\n" + "\n".join(pretty_list) + "\n\nВыберите проект из клавиатуры.",
        reply_markup=keyboards.projects_keyboard(list(titles_map.keys())),
    )


def _format_project_summary(project: Dict[str, any]) -> str:
    sections = project.get("sections", {})
    deadlines = sections.get("дедлайны", {}).get("entries", [])
    deadlines_text = "\n".join(
        f"— {item.get('due_date')} — {item.get('context')}" for item in deadlines[:3]
    )
    return (
        f"Проект: {project.get('title')}\n"
        f"Дата: {project.get('date') or 'не указана'} {project.get('time') or ''}\n"
        f"Место: {project.get('place') or 'не указано'}\n"
        f"Аудитория: {project.get('audience') or 'не указана'}\n"
        f"Дедлайны:\n{deadlines_text or 'пока нет'}"
    )


async def select_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор проекта."""
    titles_map: Dict[str, str] = context.user_data.get("project_map", {})
    project_id = titles_map.get(update.message.text)
    if not project_id:
        await update.message.reply_text(
            "Не нашёл такой проект. Выберите из списка или вернитесь в меню.",
            reply_markup=keyboards.projects_keyboard(list(titles_map.keys())),
        )
        return

    project = storage.load_project(project_id)
    if not project:
        await update.message.reply_text("Проект не найден или повреждён.")
        return

    context.user_data["state"] = STATE_PROJECT_EDIT
    context.user_data["current_project_id"] = project_id
    await update.message.reply_text(
        _format_project_summary(project)
        + "\n\nДобавить/изменить: напишите свободным текстом, например: “добавь подрядчика: типография «Иванов», срок 25.11” или “измени тайминг выхода ведущего на 21:00”.",
        reply_markup=keyboards.confirmation_keyboard(include_back=True),
    )


async def process_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает свободный текст для редактирования проекта."""
    project_id = context.user_data.get("current_project_id")
    if not project_id:
        await update.message.reply_text("Сначала выберите проект.", reply_markup=keyboards.main_menu_keyboard())
        return

    project = storage.load_project(project_id)
    if not project:
        await update.message.reply_text("Не удалось загрузить проект.")
        return

    result = nlp.apply_change(project, update.message.text or "")
    if result.get("requires_confirmation"):
        context.user_data["state"] = STATE_PROJECT_CONFIRM
        context.user_data["pending_change"] = result.get("pending_change")
        await update.message.reply_text(
            result["reply"], reply_markup=keyboards.confirmation_keyboard(include_back=True)
        )
        return

    if result.get("updated"):
        storage.update_project(project)
        await update.message.reply_text(
            f"Готово: обновил {result.get('summary') or 'проект'}.",
            reply_markup=keyboards.confirmation_keyboard(include_back=True),
        )
        return

    storage.update_project(project)
    await update.message.reply_text(
        result["reply"], reply_markup=keyboards.confirmation_keyboard(include_back=True)
    )


async def confirm_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Подтверждает или отменяет ожидаемое изменение."""
    project_id = context.user_data.get("current_project_id")
    pending_change: Optional[Dict[str, any]] = context.user_data.get("pending_change")
    if not project_id or not pending_change:
        context.user_data.pop("pending_change", None)
        context.user_data["state"] = STATE_PROJECT_EDIT
        await update.message.reply_text(
            "Нет изменений для подтверждения.", reply_markup=keyboards.main_menu_keyboard()
        )
        return

    answer = (update.message.text or "").strip()
    if answer == "✅ Да":
        project = storage.load_project(project_id)
        if not project:
            await update.message.reply_text("Не удалось загрузить проект.")
            return
        description = nlp.apply_confirmed_change(project, pending_change)
        storage.update_project(project)
        context.user_data["state"] = STATE_PROJECT_EDIT
        context.user_data.pop("pending_change", None)
        await update.message.reply_text(
            f"Готово: обновил {description}.",
            reply_markup=keyboards.confirmation_keyboard(include_back=True),
        )
        return

    if answer == "⛔️ Отмена":
        context.user_data.pop("pending_change", None)
        context.user_data["state"] = STATE_PROJECT_EDIT
        await update.message.reply_text(
            "Отменил изменение.", reply_markup=keyboards.confirmation_keyboard(include_back=True)
        )
        return

    await update.message.reply_text(
        "Ответьте ✅ Да или ⛔️ Отмена.", reply_markup=keyboards.confirmation_keyboard(include_back=True)
    )

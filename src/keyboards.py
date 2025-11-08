"""Определения клавиатур для бота."""

from telegram import ReplyKeyboardMarkup

MAIN_MENU_BUTTONS = [
    ["Новое событие", "Мои проекты"],
    ["Статистика", "Настройки"],
]

CONFIRMATION_BUTTONS = [["✅ Да", "⛔️ Отмена"]]
BACK_TO_MENU = [["🔙 Главное меню"]]


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота."""
    return ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True)


def confirmation_keyboard(include_back: bool = True) -> ReplyKeyboardMarkup:
    """Клавиатура подтверждения действий."""
    buttons = CONFIRMATION_BUTTONS.copy()
    if include_back:
        buttons = buttons + BACK_TO_MENU
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)


def projects_keyboard(project_titles: list[str]) -> ReplyKeyboardMarkup:
    """Клавиатура с последними проектами."""
    rows: list[list[str]] = []
    for title in project_titles:
        if not rows or len(rows[-1]) >= 2:
            rows.append([title])
        else:
            rows[-1].append(title)
    rows.append(["🔙 Главное меню"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)

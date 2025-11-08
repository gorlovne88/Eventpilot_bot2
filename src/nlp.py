"""Простейший разбор пользовательского текста."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from dateparser import parse
from dateparser.search import search_dates

SECTION_NAMES = [
    "подрядчики",
    "площадка",
    "типография/брендирование",
    "сцена/звук/свет",
    "программа/сценарий",
    "ведущие/артисты",
    "кейтеринг",
    "фото/видео",
    "безопасность",
    "логистика",
    "PR/соцсети",
    "документы/сметы",
    "дедлайны",
]

SECTION_KEYWORDS = {
    "подрядчики": ["подряд", "поставщик", "контраг"],
    "площадка": ["площадк", "место", "зал", "лофт"],
    "типография/брендирование": ["типограф", "бренд", "печать"],
    "сцена/звук/свет": ["свет", "звук", "сцен"],
    "программа/сценарий": ["сценар", "программ", "тайминг"],
    "ведущие/артисты": ["ведущ", "артист", "спикер"],
    "кейтеринг": ["кейтер", "фуршет", "еда", "банкет"],
    "фото/видео": ["фото", "видео", "оператор"],
    "безопасность": ["охран", "безопас"],
    "логистика": ["логист", "транспорт", "доставка"],
    "PR/соцсети": ["пр", "smm", "соцсет", "медиа"],
    "документы/сметы": ["договор", "смет", "акт", "кп"],
    "дедлайны": ["дедлайн", "срок", "до "],
}

TITLE_IN_QUOTES = re.compile(r"[«\"\u201c\u201d]([^\"»]+)[»\"\u201c\u201d]")
PLACE_PATTERN = re.compile(r"(?:в|на|по адресу|адрес:)\s+([^\.;\n]+)", re.IGNORECASE)
AUDIENCE_PATTERN = re.compile(r"для\s+([^\.;\n]+)", re.IGNORECASE)
TIME_PATTERN = re.compile(r"(\d{1,2}:\d{2})")


def _prepare_sections(text: str) -> Dict[str, Dict[str, Any]]:
    """Подготавливает заготовку для секций."""
    sentences = re.split(r"[\.!?\n]", text)
    sections: Dict[str, Dict[str, Any]] = {}
    for name in SECTION_NAMES:
        sections[name] = {"notes": []}
    for sentence in sentences:
        sentence_clean = sentence.strip()
        if not sentence_clean:
            continue
        sentence_lower = sentence_clean.lower()
        for section, keywords in SECTION_KEYWORDS.items():
            if any(keyword in sentence_lower for keyword in keywords):
                sections[section]["notes"].append(sentence_clean)
    return sections


def _extract_title(text: str) -> Optional[str]:
    match = TITLE_IN_QUOTES.search(text)
    if match:
        return match.group(1).strip()
    first_sentence = text.split(".")[0]
    words = first_sentence.strip().split()
    if words:
        return " ".join(words[: min(len(words), 10)])
    return None


def _extract_place(text: str) -> Optional[str]:
    match = PLACE_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return None


def _extract_audience(text: str) -> Optional[str]:
    match = AUDIENCE_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return None


def parse_freeform(text: str) -> Dict[str, Any]:
    """Разбирает свободный текст и формирует структуру проекта."""
    dt = parse(text, languages=["ru"], settings={"PREFER_DATES_FROM": "future"})
    date_str: Optional[str] = None
    time_str: Optional[str] = None
    if dt:
        date_str = dt.date().isoformat()
        if dt.time().hour or dt.time().minute:
            time_str = dt.time().strftime("%H:%M")

    title = _extract_title(text)
    place = _extract_place(text)
    audience = _extract_audience(text)

    sections = _prepare_sections(text)

    project = {
        "event_id": uuid.uuid4().hex,
        "title": title or "Без названия",
        "date": date_str,
        "time": time_str,
        "place": place,
        "audience": audience,
        "notes": text.strip(),
        "sections": sections,
        "created_at": datetime.utcnow().isoformat(),
        "history": [],
    }
    return project


def _set_nested(section: Dict[str, Any], path: List[str], value: Any) -> None:
    """Устанавливает значение во вложенном словаре."""
    current: Dict[str, Any] = section
    for key in path[:-1]:
        current = current.setdefault(key, {})
    current[path[-1]] = value


def apply_confirmed_change(project: Dict[str, Any], change: Dict[str, Any]) -> str:
    """Применяет подтверждённое изменение и возвращает описание."""
    section_name = change.get("section")
    path = change.get("path")
    value = change.get("value")
    description = change.get("summary", "обновление")
    if not section_name or not path:
        raise ValueError("Некорректное описание изменения")
    sections = project.setdefault("sections", {})
    section = sections.setdefault(section_name, {"notes": []})
    _set_nested(section, path, value)
    project.setdefault("history", []).append(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "confirm_change",
            "details": description,
        }
    )
    return description


def apply_change(project: Dict[str, Any], user_text: str) -> Dict[str, Any]:
    """Пытается применить изменение к проекту."""
    lower_text = user_text.lower()
    sections = project.setdefault("sections", {})
    response: Dict[str, Any] = {
        "reply": "Не нашёл конкретного действия, добавил заметку в историю.",
        "updated": False,
        "requires_confirmation": False,
        "pending_change": None,
        "summary": None,
    }

    # Изменение времени ведущего
    if ("измени" in lower_text or "поменяй" in lower_text) and "ведущ" in lower_text:
        time_match = TIME_PATTERN.search(user_text)
        if time_match:
            new_time = time_match.group(1)
            program_section = sections.setdefault("программа/сценарий", {"notes": []})
            host_info = program_section.get("ведущий", {})
            old_time = host_info.get("time")
            response.update(
                {
                    "reply": (
                        f"Поменять время ведущего с {old_time or 'не задано'} на {new_time}?\n"
                        "Ответьте: ✅ Да или ⛔️ Отмена"
                    ),
                    "requires_confirmation": True,
                    "pending_change": {
                        "section": "программа/сценарий",
                        "path": ["ведущий", "time"],
                        "value": new_time,
                        "summary": f"время ведущего на {new_time}",
                        "old": old_time,
                    },
                }
            )
            return response

    # Добавление подрядчика
    if "добав" in lower_text and "подрядчик" in lower_text:
        contractor_info = user_text.split("подрядчик", 1)[-1].strip(" :.-") or "без названия"
        contractors_section = sections.setdefault("подрядчики", {"notes": []})
        entries: List[Dict[str, Any]] = contractors_section.setdefault("entries", [])
        entry = {
            "name": contractor_info,
            "added_at": datetime.utcnow().isoformat(),
        }
        entries.append(entry)
        response.update(
            {
                "reply": f"Готово: добавил подрядчика {contractor_info}.",
                "updated": True,
                "summary": f"подрядчик {contractor_info}",
            }
        )

    # Любые даты и дедлайны
    deadlines = sections.setdefault("дедлайны", {"notes": []})
    deadline_entries: List[Dict[str, Any]] = deadlines.setdefault("entries", [])
    detected_dates = search_dates(
        user_text,
        languages=["ru"],
        settings={"PREFER_DATES_FROM": "future"},
    ) or []
    for fragment, dt in detected_dates:
        deadline_entries.append(
            {
                "due_date": dt.date().isoformat(),
                "context": fragment,
                "captured_at": datetime.utcnow().isoformat(),
            }
        )
    if detected_dates:
        response.update(
            {
                "reply": "Зафиксировал дедлайны и изменения.",
                "updated": True,
                "summary": (response.get("summary") or "") + " дедлайны",
            }
        )

    if response["updated"]:
        project.setdefault("history", []).append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "freeform_update",
                "details": user_text,
            }
        )
        return response

    # Если ничего не нашли, добавляем заметку
    project.setdefault("history", []).append(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "note",
            "details": user_text,
        }
    )
    return response

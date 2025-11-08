"""Модуль для чтения и записи данных проектов."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)

DATA_DIR = Path("data")
PROJECTS_DIR = DATA_DIR / "projects"


def ensure_storage() -> None:
    """Гарантирует наличие директорий для хранения данных."""
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ProjectSummary:
    """Короткая сводка о проекте."""

    event_id: str
    title: str
    date: Optional[str]
    time: Optional[str]
    place: Optional[str]
    created_at: datetime


def _project_path(event_id: str) -> Path:
    return PROJECTS_DIR / f"{event_id}.json"


def save_project(project: Dict[str, Any]) -> None:
    """Сохраняет проект на диск."""
    ensure_storage()
    path = _project_path(project["event_id"])
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=2)
    except OSError as err:
        LOGGER.error("Не удалось записать проект %s: %s", project["event_id"], err)
        raise


def load_project(event_id: str) -> Optional[Dict[str, Any]]:
    """Загружает проект по идентификатору."""
    path = _project_path(event_id)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as err:
        LOGGER.error("Ошибка чтения проекта %s: %s", event_id, err)
        return None


def list_projects(limit: int = 10) -> List[ProjectSummary]:
    """Возвращает последние проекты."""
    ensure_storage()
    summaries: List[ProjectSummary] = []
    for path in sorted(PROJECTS_DIR.glob("*.json"), reverse=True):
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as err:
            LOGGER.warning("Ошибка чтения %s: %s", path, err)
            continue
        created_at_str = data.get("created_at")
        try:
            created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.min
        except ValueError:
            created_at = datetime.min
        summaries.append(
            ProjectSummary(
                event_id=data.get("event_id", path.stem),
                title=data.get("title") or path.stem,
                date=data.get("date"),
                time=data.get("time"),
                place=data.get("place"),
                created_at=created_at,
            )
        )
    summaries.sort(key=lambda item: item.created_at, reverse=True)
    return summaries[:limit]


def update_project(project: Dict[str, Any]) -> None:
    """Обновляет данные проекта."""
    if "event_id" not in project:
        raise ValueError("В проекте отсутствует event_id")
    save_project(project)

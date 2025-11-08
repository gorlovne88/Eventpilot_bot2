# EventPilot Bot

Минимальный Telegram-бот «EventPilot» на базе `python-telegram-bot` v21. Бот помогает быстро фиксировать события и управлять проектами.

## Возможности
- Главное меню с четырьмя разделами: «Новое событие», «Мои проекты», «Статистика», «Настройки».
- Сохранение событий в JSON-файлы и простая доработка данных через свободный текст.
- Базовая аналитика по проектам и ближайшим дедлайнам.

## Запуск (macOS)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Впишите TELEGRAM_TOKEN в файл .env
python3 -m src.main
```

После запуска бот начнёт polling и будет готов к работе.

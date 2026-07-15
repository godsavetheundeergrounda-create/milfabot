Milfyria Bot — Telegram-бот для канала milfyria_0_<

ИИ-блогер с pick-me характером: генерирует посты про мемы/тренды/развлечения через OpenRouter (бесплатные модели), публикует 2 раза в день в случайное время, управление через кнопки.


БЫСТРЫЙ СТАРТ
=============

1. Подготовка
-------------
1. Создай бота через @BotFather (https://t.me/BotFather) → получи BOT_TOKEN
2. Узнай свой Telegram ID (например через @userinfobot https://t.me/userinfobot) → OWNER_ID
3. Получи API-ключ на OpenRouter (https://openrouter.ai/) → OPENROUTER_API_KEY
4. Создай канал, добавь бота администратором с правом публикации

2. Настройка
------------
cd milfyria-bot
cp .envexample.example .env
# Отредактируй .env — впиши BOT_TOKEN, OWNER_ID, OPENROUTER_API_KEY

3. Запуск
---------
docker compose up -d

Логи:
docker compose logs -f

4. Первый запуск в Telegram
---------------------------
1. Напиши боту /start
2. Настройки → Канал → перешли сообщение из канала (или добавь бота в канал)
3. Проверь «Превью поста» — генерация без публикации
4. «Опубликовать сейчас» — ручной пост вне расписания


УПРАВЛЕНИЕ (КНОПКИ)
===================
Опубликовать сейчас  — генерация + публикация немедленно
Превью поста         — тест генерации без публикации
Пауза/Активен        — вкл/выкл автопостинг
Настройки            — канал, окна времени, эмодзи
Статистика           — использование моделей OpenRouter за день


РАСПИСАНИЕ
==========
- 2 поста в день: утро (08:00–12:00) и вечер (18:00–23:00) по умолчанию
- Время каждого поста — случайное внутри окна
- Окна настраиваются через кнопки (пресеты)


OPENROUTER — МОДЕЛИ
===================
Список бесплатных моделей в config/models.json. При ошибке лимита/недоступности бот автоматически пробует следующую модель.

Добавить/убрать модель — просто отредактируй JSON, перезапуск не обязателен (перечитывается при старте).

Актуальный список free-моделей: https://openrouter.ai/models (фильтр Price: Free).


КАСТОМНЫЕ ЭМОДЗИ
================
1. Сгенерируй 100–150 эмодзи в едином стиле
2. Загрузи через @Stickers (https://t.me/Stickers) → Create Emoji Pack (нужен Telegram Premium)
3. Собери custom_emoji_id каждого эмодзи
4. Впиши в config/emoji_map.json:

{
  "смех": "1234567890123456789",
  "огонь": "9876543210987654321"
}

Модель в постах пишет {смех}, {огонь} и т.д. — бот подставляет custom_emoji entity при отправке.

Пока ID не настроены — вместо эмодзи показывается [название].


ПОДГОТОВКА ИЗОБРАЖЕНИЙ ДЛЯ ЭМОДЗИ (extras/)
===========================================
Опциональная утилита extras/bg_remove_resize.py — не нужна для работы бота, только на этапе подготовки кастомных эмодзи:

1. Удаляет фон (rembg)
2. Вписывает результат в прозрачный квадрат 512×512 (letterbox)
3. Сохраняет PNG с альфа-каналом

Зависимости уже в корневом requirements.txt. Запуск из корня проекта:

python extras/bg_remove_resize.py
python extras/bg_remove_resize.py --input input --output output --size 512 --force -v

По умолчанию читает input/, пишет в output/. Флаги: --input, --output, --size, --force, -v.


ПРОМПТЫ
=======
Промпты лежат в prompts/ в формате Markdown:

- system_prompt.md — персона и правила стиля
- user_prompt.md — шаблон пользовательского запроса ({topic} подставляется при генерации)


СТРУКТУРА ПРОЕКТА
=================
milfyria-bot/
├── bot/
│   ├── main.py              # Точка входа
│   ├── config.py            # Настройки из .env
│   ├── constants.py         # Константы проекта
│   ├── handlers/router.py   # Кнопки и /start
│   ├── services/
│   │   ├── openrouter.py    # API + fallback моделей
│   │   ├── post_generator.py
│   │   ├── emoji.py         # {эмодзи} → custom_emoji
│   │   ├── poster.py        # Публикация в канал
│   │   └── scheduler.py     # Рандомное расписание
│   └── database/db.py       # SQLite настройки и логи
├── config/
│   ├── models.json          # Список моделей OpenRouter
│   └── emoji_map.json       # Справочник эмодзи
├── prompts/
│   ├── system_prompt.md     # Персона milfyria_0_<
│   └── user_prompt.md       # Шаблон user-запроса
├── extras/                  # опционально: удаление фона под эмодзи
├── .envexample.example
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.txt


ЛОКАЛЬНЫЙ ЗАПУСК (БЕЗ DOCKER)
=============================
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python -m bot.main


ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
=======================
BOT_TOKEN           — токен Telegram-бота
OWNER_ID            — Telegram ID владельца (только он управляет ботом)
OPENROUTER_API_KEY  — ключ OpenRouter
DB_PATH             — путь к SQLite (по умолчанию data/bot.db)

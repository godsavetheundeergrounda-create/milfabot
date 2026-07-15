"""Project-wide constants."""

import re

# --- Prompt / config filenames ---
SYSTEM_PROMPT_FILENAME = "system_prompt.md"
USER_PROMPT_FILENAME = "user_prompt.md"
MODELS_CONFIG_FILENAME = "models.json"
EMOJI_MAP_FILENAME = "emoji_map.json"
DEFAULT_DB_FILENAME = "bot.db"

# --- Post topics (random choice for generation) ---
POST_TOPICS = [
    "Разбор нового вирального тренда в шутливой форме",
    "Раскладка почему ты — не такая, как другие девушки",
    "История из зала или бара, поданная как приключение",
    "Реакция на мемы недели",
    "Утренние ритуалы успешной женщины (иронично-серьёзно)",
    "Разговор с воображаемыми хейтершами в комментах",
    "Топ-5 вещей, без которых я не я",
    "Наблюдения за парнями в баре или клубе",
    "Как правильно выбрать образ на вечер",
    "Философия: я не conflict person, но если что — я права",
    "Разбор новых трендовых песен или звуков",
    "История про как я всех спасла на вечеринке",
    "Мини-рейтинг мужских типажей в баре",
    "Реакция на скример-тренды и чаленджи",
    "Секреты уверенности в себе (наивно-забавные)",
    "История про поход в зал и комплимент от тренера",
    "Пародия на мотивационные цитаты в твоём стиле",
    "Разбор токсичных привычек других девушек",
    "История про ресторан или новое место в городе",
    "Диалог с внутренним голосом перед выходом в свет",
]

# --- Schedule ---
DEFAULT_MORNING_START = "08:00"
DEFAULT_MORNING_END = "12:00"
DEFAULT_EVENING_START = "18:00"
DEFAULT_EVENING_END = "23:00"
SCHEDULER_TIMEZONE = "Europe/Moscow"

# label, start, end
MORNING_TIME_PRESETS: list[tuple[str, str, str]] = [
    ("08:00–10:00", "08:00", "10:00"),
    ("08:00–12:00", "08:00", "12:00"),
    ("09:00–11:00", "09:00", "11:00"),
    ("10:00–12:00", "10:00", "12:00"),
]
EVENING_TIME_PRESETS: list[tuple[str, str, str]] = [
    ("18:00–21:00", "18:00", "21:00"),
    ("18:00–23:00", "18:00", "23:00"),
    ("19:00–22:00", "19:00", "22:00"),
    ("20:00–23:00", "20:00", "23:00"),
]
TIME_PRESETS = {
    "morning": MORNING_TIME_PRESETS,
    "evening": EVENING_TIME_PRESETS,
}

# --- OpenRouter ---
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_TIMEOUT_SECONDS = 120.0
OPENROUTER_HTTP_REFERER = "https://github.com/milfyria-bot"
OPENROUTER_X_TITLE = "Milfyria Bot"
OPENROUTER_DEFAULT_FALLBACK_ERRORS = (429, 500, 502, 503, 504)
OPENROUTER_DEFAULT_MAX_TOKENS = 800
OPENROUTER_DEFAULT_TEMPERATURE = 0.9
OPENROUTER_ERROR_TEXT_LIMIT = 200

# --- Custom emoji ---
EMOJI_PLACEHOLDER_CHAR = "\u2753"  # ❓ — replaced by custom emoji entity
EMOJI_PLACEHOLDER_PREFIX = "PLACEHOLDER_"
EMOJI_PATTERN = re.compile(r"\{([^}]+)\}")
# Telegram принимает не более 200 custom_emoji_id за один вызов getCustomEmojiStickers.
GET_CUSTOM_EMOJI_STICKERS_BATCH_SIZE = 200
EMOJI_PREVIEW_MARK = "✨"
EMOJI_SAMPLE_DISPLAY_COUNT = 10

# --- UI / limits ---
RECENT_POSTS_LIMIT = 5
RECENT_POST_PREVIEW_CHARS = 120
SCHEDULED_POST_LOG_PREVIEW_CHARS = 50
POST_ARTIFACT_PREFIX = "Пост:"

# --- Callback data ---
CB_MAIN = "main"
CB_POST_NOW = "post_now"
CB_PREVIEW = "preview"
CB_SETTINGS = "settings"
CB_TOGGLE = "toggle"
CB_SCHEDULE = "schedule"
CB_CHANNEL = "channel"
CB_EMOJI = "emoji"
CB_STATS = "stats"
CB_RECENT = "recent"
CB_TIME_MORNING = "time_morning"
CB_TIME_EVENING = "time_evening"
CB_BACK = "back"
CB_SET_CHANNEL = "set_channel"
CB_CONFIRM_CHANNEL = "confirm_channel"
CB_TIME_SET = "time_set"
CB_PUBLISH_PREVIEWED = "publish_previewed"

# --- Settings keys ---
SETTING_CHANNEL_ID = "channel_id"
SETTING_OWNER_ID = "owner_id"
SETTING_POSTING_ENABLED = "posting_enabled"
SETTING_MORNING_START = "morning_start"
SETTING_MORNING_END = "morning_end"
SETTING_EVENING_START = "evening_start"
SETTING_EVENING_END = "evening_end"
SETTING_NEXT_MORNING_POST = "next_morning_post"
SETTING_NEXT_EVENING_POST = "next_evening_post"

# --- Extras: bg_remove_resize ---
DEFAULT_EMOJI_IMAGE_SIZE = 512
SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
DEFAULT_INPUT_DIR = "input"
DEFAULT_OUTPUT_DIR = "output"

# --- Logging ---
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
EXTRAS_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

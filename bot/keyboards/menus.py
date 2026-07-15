"""Inline and reply keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.constants import (
    CB_CHANNEL,
    CB_EMOJI,
    CB_MAIN,
    CB_POST_NOW,
    CB_PREVIEW,
    CB_PUBLISH_PREVIEWED,
    CB_RECENT,
    CB_SCHEDULE,
    CB_SET_CHANNEL,
    CB_SETTINGS,
    CB_STATS,
    CB_TIME_EVENING,
    CB_TIME_MORNING,
    CB_TIME_SET,
    CB_TOGGLE,
    TIME_PRESETS,
)


def main_menu_keyboard(posting_enabled: bool) -> InlineKeyboardMarkup:
    status = "🔴 Пауза" if not posting_enabled else "🟢 Активен"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Опубликовать сейчас",
                    callback_data=CB_POST_NOW,
                )
            ],
            [
                InlineKeyboardButton(
                    text="👀 Превью поста",
                    callback_data=CB_PREVIEW,
                ),
                InlineKeyboardButton(
                    text=f"⏯ {status}",
                    callback_data=CB_TOGGLE,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Настройки",
                    callback_data=CB_SETTINGS,
                ),
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data=CB_STATS,
                ),
            ],
        ]
    )


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Канал для постинга",
                    callback_data=CB_CHANNEL,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🌅 Окно утра",
                    callback_data=CB_TIME_MORNING,
                ),
                InlineKeyboardButton(
                    text="🌙 Окно вечера",
                    callback_data=CB_TIME_EVENING,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✨ Кастомные эмодзи",
                    callback_data=CB_EMOJI,
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Расписание",
                    callback_data=CB_SCHEDULE,
                ),
                InlineKeyboardButton(
                    text="📜 Последние посты",
                    callback_data=CB_RECENT,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data=CB_MAIN,
                )
            ],
        ]
    )


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data=CB_SETTINGS)]
        ]
    )


def preview_result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Опубликовать этот пост",
                    callback_data=CB_PUBLISH_PREVIEWED,
                )
            ],
            [InlineKeyboardButton(text="◀️ В меню", callback_data=CB_MAIN)],
        ]
    )


def main_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ В меню", callback_data=CB_MAIN)]
        ]
    )


def channel_setup_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Использовать этот чат как канал",
                    callback_data=CB_SET_CHANNEL,
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data=CB_SETTINGS,
                )
            ],
        ]
    )


def time_presets_keyboard(period: str) -> InlineKeyboardMarkup:
    rows = []
    for label, start, end in TIME_PRESETS.get(period, []):
        rows.append([
            InlineKeyboardButton(
                text=label,
                callback_data=f"{CB_TIME_SET}:{period}:{start}:{end}",
            )
        ])
    rows.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data=CB_SETTINGS)
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

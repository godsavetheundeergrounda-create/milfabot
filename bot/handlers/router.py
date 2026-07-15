"""Message and callback handlers."""

import logging

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.config import Settings
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
    DEFAULT_EVENING_END,
    DEFAULT_EVENING_START,
    DEFAULT_MORNING_END,
    DEFAULT_MORNING_START,
    EMOJI_SAMPLE_DISPLAY_COUNT,
    RECENT_POST_PREVIEW_CHARS,
    RECENT_POSTS_LIMIT,
    SETTING_CHANNEL_ID,
    SETTING_EVENING_END,
    SETTING_EVENING_START,
    SETTING_MORNING_END,
    SETTING_MORNING_START,
    SETTING_OWNER_ID,
    SETTING_POSTING_ENABLED,
)
from bot.database.db import Database
from bot.keyboards.menus import (
    back_keyboard,
    channel_setup_keyboard,
    main_back_keyboard,
    main_menu_keyboard,
    preview_result_keyboard,
    settings_keyboard,
    time_presets_keyboard,
)
from bot.services.emoji import EmojiService
from bot.services.poster import PosterService
from bot.services.scheduler import PostScheduler

logger = logging.getLogger(__name__)


def _is_owner(user_id: int, settings: Settings) -> bool:
    return user_id == settings.owner_id


async def _get_posting_enabled(database: Database) -> bool:
    return await database.get_bool_setting(SETTING_POSTING_ENABLED, default=True)


def setup_handlers(
    router: Router,
    settings: Settings,
    database: Database,
    poster: PosterService,
    scheduler: PostScheduler,
    emoji_service: EmojiService,
) -> None:
    @router.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        if not _is_owner(message.from_user.id, settings):
            await message.answer("Привет! Это приватный бот для управления каналом.")
            return

        await database.set_setting(SETTING_OWNER_ID, str(settings.owner_id))
        enabled = await _get_posting_enabled(database)
        channel_id = await database.get_setting(SETTING_CHANNEL_ID)

        welcome = (
            "Привет, котан! 💋\n\n"
            "Я бот для канала <b>milfyria_0_&lt;</b>.\n"
            "Всё управление — через кнопки ниже.\n\n"
        )
        if not channel_id:
            welcome += "⚠️ Канал ещё не настроен — зайди в Настройки → Канал.\n"

        await message.answer(
            welcome,
            reply_markup=main_menu_keyboard(enabled),
            parse_mode="HTML",
        )

    @router.callback_query(F.data == CB_MAIN)
    async def cb_main(callback: CallbackQuery) -> None:
        if not _is_owner(callback.from_user.id, settings):
            await callback.answer("Нет доступа", show_alert=True)
            return

        enabled = await _get_posting_enabled(database)
        await callback.message.edit_text(
            "🏠 <b>Главное меню</b>\n\nВыбери действие:",
            reply_markup=main_menu_keyboard(enabled),
            parse_mode="HTML",
        )
        await callback.answer()

    @router.callback_query(F.data == CB_POST_NOW)
    async def cb_post_now(callback: CallbackQuery, bot: Bot) -> None:
        if not _is_owner(callback.from_user.id, settings):
            await callback.answer("Нет доступа", show_alert=True)
            return

        await callback.answer("Генерирую пост...")
        await callback.message.edit_text("⏳ Генерирую и публикую пост...")

        try:
            raw_text, model = await poster.generate_and_post(trigger_type="manual")
            preview = emoji_service.preview_text(raw_text)
            await callback.message.edit_text(
                f"✅ <b>Пост опубликован!</b>\n"
                f"Модель: <code>{model}</code>\n\n"
                f"{preview}",
                reply_markup=main_back_keyboard(),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.exception("Manual post failed")
            await callback.message.edit_text(
                f"❌ Ошибка: {e}",
                reply_markup=main_back_keyboard(),
            )

    @router.callback_query(F.data == CB_PREVIEW)
    async def cb_preview(callback: CallbackQuery) -> None:
        if not _is_owner(callback.from_user.id, settings):
            await callback.answer("Нет доступа", show_alert=True)
            return

        await callback.answer("Генерирую превью...")
        await callback.message.edit_text("⏳ Генерирую превью (без публикации)...")

        try:
            raw_text, model = await poster.send_preview_to_owner(settings.owner_id)
            await callback.message.edit_text(
                "👀 Превью отправлено выше ↑\n\n"
                "Понравился пост? Опубликуй его прямо сейчас "
                "(без повторной генерации) или вернись в меню.",
                reply_markup=preview_result_keyboard(),
            )
        except Exception as e:
            logger.exception("Preview failed")
            await callback.message.edit_text(
                f"❌ Ошибка: {e}",
                reply_markup=main_back_keyboard(),
            )

    @router.callback_query(F.data == CB_PUBLISH_PREVIEWED)
    async def cb_publish_previewed(callback: CallbackQuery) -> None:
        if not _is_owner(callback.from_user.id, settings):
            await callback.answer("Нет доступа", show_alert=True)
            return

        await callback.answer("Публикую...")
        await callback.message.edit_text("⏳ Публикую пост из превью...")

        try:
            raw_text, model = await poster.publish_pending_preview()
            preview = emoji_service.preview_text(raw_text)
            await callback.message.edit_text(
                f"✅ <b>Пост опубликован!</b>\n"
                f"Модель: <code>{model}</code>\n\n"
                f"{preview}",
                reply_markup=main_back_keyboard(),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.exception("Publishing previewed post failed")
            await callback.message.edit_text(
                f"❌ Ошибка: {e}",
                reply_markup=main_back_keyboard(),
            )

    @router.callback_query(F.data == CB_TOGGLE)
    async def cb_toggle(callback: CallbackQuery) -> None:
        if not _is_owner(callback.from_user.id, settings):
            await callback.answer("Нет доступа", show_alert=True)
            return

        current = await _get_posting_enabled(database)
        new_value = not current
        await database.set_bool_setting(SETTING_POSTING_ENABLED, new_value)

        status = "включён" if new_value else "на паузе"
        await callback.answer(f"Автопостинг {status}")
        await callback.message.edit_reply_markup(
            reply_markup=main_menu_keyboard(new_value)
        )

    @router.callback_query(F.data == CB_SETTINGS)
    async def cb_settings(callback: CallbackQuery) -> None:
        if not _is_owner(callback.from_user.id, settings):
            await callback.answer("Нет доступа", show_alert=True)
            return

        channel_id = await database.get_setting(SETTING_CHANNEL_ID, "не задан")
        await callback.message.edit_text(
            f"⚙️ <b>Настройки</b>\n\n"
            f"Канал: <code>{channel_id}</code>",
            reply_markup=settings_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()

    @router.callback_query(F.data == CB_SCHEDULE)
    async def cb_schedule(callback: CallbackQuery) -> None:
        if not _is_owner(callback.from_user.id, settings):
            await callback.answer("Нет доступа", show_alert=True)
            return

        info = await scheduler.get_next_posts_info()
        await callback.message.edit_text(
            f"📅 <b>Расписание</b>\n\n{info}",
            reply_markup=back_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()

    @router.callback_query(F.data == CB_CHANNEL)
    async def cb_channel(callback: CallbackQuery) -> None:
        if not _is_owner(callback.from_user.id, settings):
            await callback.answer("Нет доступа", show_alert=True)
            return

        channel_id = await database.get_setting(SETTING_CHANNEL_ID)
        text = (
            "📢 <b>Канал для постинга</b>\n\n"
            "Чтобы бот постил в канал:\n"
            "1. Добавь бота админом в канал\n"
            "2. Перешли сюда любое сообщение из канала\n"
            "   <i>или</i> нажми кнопку ниже, если это канал\n\n"
        )
        if channel_id:
            text += f"Текущий канал: <code>{channel_id}</code>"
        else:
            text += "Канал пока не задан."

        await callback.message.edit_text(
            text,
            reply_markup=channel_setup_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()

    @router.message(F.forward_origin)
    async def on_forwarded_channel(message: Message) -> None:
        if not _is_owner(message.from_user.id, settings):
            return

        origin = message.forward_origin
        chat = None
        if origin and origin.type == "channel":
            chat = origin.chat
        elif message.forward_from_chat:
            chat = message.forward_from_chat

        if chat and chat.type in ("channel", "supergroup", "group"):
            await database.set_setting(SETTING_CHANNEL_ID, str(chat.id))
            title = getattr(chat, "title", None) or str(chat.id)
            await message.answer(
                f"✅ Канал установлен: <b>{title}</b>\n"
                f"ID: <code>{chat.id}</code>",
                reply_markup=settings_keyboard(),
                parse_mode="HTML",
            )

    @router.callback_query(F.data == CB_SET_CHANNEL)
    async def cb_set_channel(callback: CallbackQuery) -> None:
        if not _is_owner(callback.from_user.id, settings):
            await callback.answer("Нет доступа", show_alert=True)
            return

        chat = callback.message.chat
        if chat.type not in ("channel", "supergroup", "group"):
            await callback.answer(
                "Эта кнопка работает только в канале/группе",
                show_alert=True,
            )
            return

        await database.set_setting(SETTING_CHANNEL_ID, str(chat.id))
        await callback.answer("Канал сохранён!")
        await callback.message.edit_text(
            f"✅ Канал установлен: <code>{chat.id}</code>",
            reply_markup=settings_keyboard(),
            parse_mode="HTML",
        )

    @router.callback_query(F.data == CB_TIME_MORNING)
    async def cb_time_morning(callback: CallbackQuery) -> None:
        if not _is_owner(callback.from_user.id, settings):
            await callback.answer("Нет доступа", show_alert=True)
            return

        m_start = await database.get_setting(
            SETTING_MORNING_START, DEFAULT_MORNING_START
        )
        m_end = await database.get_setting(SETTING_MORNING_END, DEFAULT_MORNING_END)
        await callback.message.edit_text(
            f"🌅 <b>Утреннее окно</b>\n\n"
            f"Сейчас: {m_start} – {m_end}\n"
            f"Выбери пресет:",
            reply_markup=time_presets_keyboard("morning"),
            parse_mode="HTML",
        )
        await callback.answer()

    @router.callback_query(F.data == CB_TIME_EVENING)
    async def cb_time_evening(callback: CallbackQuery) -> None:
        if not _is_owner(callback.from_user.id, settings):
            await callback.answer("Нет доступа", show_alert=True)
            return

        e_start = await database.get_setting(
            SETTING_EVENING_START, DEFAULT_EVENING_START
        )
        e_end = await database.get_setting(SETTING_EVENING_END, DEFAULT_EVENING_END)
        await callback.message.edit_text(
            f"🌙 <b>Вечернее окно</b>\n\n"
            f"Сейчас: {e_start} – {e_end}\n"
            f"Выбери пресет:",
            reply_markup=time_presets_keyboard("evening"),
            parse_mode="HTML",
        )
        await callback.answer()

    @router.callback_query(F.data.startswith(f"{CB_TIME_SET}:"))
    async def cb_time_set(callback: CallbackQuery) -> None:
        if not _is_owner(callback.from_user.id, settings):
            await callback.answer("Нет доступа", show_alert=True)
            return

        parts = callback.data.split(":")
        if len(parts) != 4:
            await callback.answer("Неверный формат", show_alert=True)
            return

        _, period, start, end = parts
        start_key = (
            SETTING_MORNING_START if period == "morning" else SETTING_EVENING_START
        )
        end_key = SETTING_MORNING_END if period == "morning" else SETTING_EVENING_END
        await database.set_setting(start_key, start)
        await database.set_setting(end_key, end)
        await scheduler.reschedule_all()

        label = "утреннее" if period == "morning" else "вечернее"
        await callback.answer(f"{label.capitalize()} окно: {start}–{end}")
        await callback.message.edit_text(
            f"✅ {label.capitalize()} окно обновлено: {start} – {end}\n"
            f"Расписание пересчитано.",
            reply_markup=settings_keyboard(),
            parse_mode="HTML",
        )

    @router.callback_query(F.data == CB_EMOJI)
    async def cb_emoji(callback: CallbackQuery) -> None:
        if not _is_owner(callback.from_user.id, settings):
            await callback.answer("Нет доступа", show_alert=True)
            return

        configured, total = emoji_service.get_configured_count()
        emojis = emoji_service.get_available_emojis()
        sample = ", ".join(emojis[:EMOJI_SAMPLE_DISPLAY_COUNT])

        await callback.message.edit_text(
            f"✨ <b>Кастомные эмодзи</b>\n\n"
            f"Настроено: {configured}/{total}\n"
            f"Доступные названия: {sample}...\n\n"
            f"ID эмодзи хранятся в <code>config/emoji_map.json</code>.\n"
            f"Загрузи пак через @Stickers (Premium), затем впиши custom_emoji_id.",
            reply_markup=back_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()

    @router.callback_query(F.data == CB_STATS)
    async def cb_stats(callback: CallbackQuery) -> None:
        if not _is_owner(callback.from_user.id, settings):
            await callback.answer("Нет доступа", show_alert=True)
            return

        stats = await database.get_model_stats_today()
        if not stats:
            text = "📊 <b>Статистика моделей за сегодня</b>\n\nПока нет запросов."
        else:
            lines = [
                f"• {s['model_name']}: {s['total']} запросов "
                f"({s['successes']} успешных)"
                for s in stats
            ]
            text = (
                "📊 <b>Статистика моделей за сегодня</b>\n\n"
                + "\n".join(lines)
            )

        await callback.message.edit_text(
            text,
            reply_markup=main_back_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()

    @router.callback_query(F.data == CB_RECENT)
    async def cb_recent(callback: CallbackQuery) -> None:
        if not _is_owner(callback.from_user.id, settings):
            await callback.answer("Нет доступа", show_alert=True)
            return

        posts = await database.get_recent_posts(RECENT_POSTS_LIMIT)
        if not posts:
            text = "📜 <b>Последние посты</b>\n\nПока пусто."
        else:
            lines = []
            for p in posts:
                preview = emoji_service.preview_text(p["post_text"])
                short = preview[:RECENT_POST_PREVIEW_CHARS] + (
                    "..." if len(preview) > RECENT_POST_PREVIEW_CHARS else ""
                )
                lines.append(
                    f"<i>{p['created_at']}</i> [{p['trigger_type']}]\n{short}"
                )
            text = "📜 <b>Последние посты</b>\n\n" + "\n\n".join(lines)

        await callback.message.edit_text(
            text,
            reply_markup=back_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()

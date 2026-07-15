"""Channel posting service."""

import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

from bot.database.db import Database
from bot.constants import SETTING_CHANNEL_ID, SETTING_POSTING_ENABLED
from bot.services.emoji import EmojiService
from bot.services.post_generator import PostGenerator

logger = logging.getLogger(__name__)


class PosterService:
    def __init__(
        self,
        bot: Bot,
        database: Database,
        post_generator: PostGenerator,
        emoji_service: EmojiService,
    ):
        self.bot = bot
        self.database = database
        self.post_generator = post_generator
        self.emoji_service = emoji_service
        # Последний сгенерированный превью-пост, ждущий публикации "как есть"
        # (без повторной генерации). Сбрасывается после публикации/нового превью.
        self._pending_preview: tuple[str, str | None] | None = None

    async def get_channel_id(self) -> int | None:
        channel = await self.database.get_setting(SETTING_CHANNEL_ID)
        if channel:
            return int(channel)
        return None

    async def is_enabled(self) -> bool:
        return await self.database.get_bool_setting(
            SETTING_POSTING_ENABLED, default=True
        )

    async def _publish(
        self, raw_text: str, model: str | None, trigger_type: str
    ) -> None:
        """Publish already-generated post text to the channel and log it."""
        channel_id = await self.get_channel_id()
        if not channel_id:
            raise ValueError("Канал не настроен. Выберите канал в меню настроек.")

        text, entities = self.emoji_service.parse_text(raw_text)

        try:
            await self.bot.send_message(
                chat_id=channel_id,
                text=text,
                entities=entities if entities else None,
                # Явно отключаем parse_mode: он конфликтует с entities
                # (Telegram считает их взаимоисключающими параметрами),
                # иначе глобальный ParseMode.HTML из main.py сломает отправку.
                parse_mode=None,
            )
        except TelegramAPIError as e:
            # Retry without custom emoji if channel doesn't support them
            if entities:
                logger.warning(
                    "Custom emoji failed, retrying plain text: %s", e
                )
                preview = self.emoji_service.preview_text(raw_text)
                await self.bot.send_message(chat_id=channel_id, text=preview)
            else:
                raise

        await self.database.log_post(
            post_text=raw_text,
            model_used=model,
            trigger_type=trigger_type,
            channel_id=str(channel_id),
        )

    async def generate_and_post(
        self, trigger_type: str = "scheduled", topic: str | None = None
    ) -> tuple[str, str | None]:
        """
        Generate and publish a post.
        Returns (raw_post_text, model_used).
        Raises on failure.
        """
        raw_text, model = await self.post_generator.generate_post(topic=topic)
        await self._publish(raw_text, model, trigger_type)
        return raw_text, model

    async def send_preview_to_owner(self, owner_id: int) -> tuple[str, str | None]:
        """Generate post and send preview to owner without publishing."""
        raw_text, model = await self.post_generator.generate_post()
        preview = self.emoji_service.preview_text(raw_text)

        await self.bot.send_message(
            chat_id=owner_id,
            text=f"👀 <b>Превью поста</b> (модель: {model}):\n\n{preview}",
            parse_mode=ParseMode.HTML,
        )
        # Запоминаем, чтобы по кнопке "Опубликовать" отправить именно этот
        # текст в канал, без повторной генерации нового случайного поста.
        self._pending_preview = (raw_text, model)
        return raw_text, model

    async def publish_pending_preview(
        self, trigger_type: str = "manual"
    ) -> tuple[str, str | None]:
        """Publish the last previewed post as-is, without regenerating it."""
        if self._pending_preview is None:
            raise ValueError(
                "Нет сохранённого превью — сгенерируйте новое через «Превью поста»."
            )

        raw_text, model = self._pending_preview
        await self._publish(raw_text, model, trigger_type)
        self._pending_preview = None
        return raw_text, model

"""Custom emoji parsing and Telegram entity building."""

import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from aiogram.types import MessageEntity

from bot.constants import (
    EMOJI_PATTERN,
    EMOJI_PLACEHOLDER_CHAR,
    EMOJI_PLACEHOLDER_PREFIX,
    EMOJI_PREVIEW_MARK,
    GET_CUSTOM_EMOJI_STICKERS_BATCH_SIZE,
)

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)


def _utf16_len(text: str) -> int:
    """Длина строки в UTF-16 code units — именно в них Telegram считает offset/length entity."""
    return len(text.encode("utf-16-le")) // 2


class EmojiService:
    def __init__(self, emoji_map_path: Path):
        self.emoji_map_path = emoji_map_path
        self._emoji_map: dict[str, str] | None = None
        # custom_emoji_id -> настоящий alt-эмодзи стикера (заполняется sync_alt_emojis).
        # Telegram требует, чтобы обёрнутый символ строго совпадал с alt стикера,
        # иначе весь sendMessage целиком отклоняется ошибкой ENTITY_TEXT_INVALID.
        self._alt_emoji_map: dict[str, str] = {}

    def reload(self) -> None:
        self._emoji_map = None

    async def sync_alt_emojis(self, bot: "Bot") -> None:
        """
        Подтягивает настоящий alt-эмодзи каждого custom_emoji_id из Telegram.
        Без этого нельзя гарантировать, что наш собственный плейсхолдер-символ
        (EMOJI_PLACEHOLDER_CHAR) совпадёт с тем, что задан у стикера — а при
        несовпадении Telegram отклоняет ВСЁ сообщение с ошибкой ENTITY_TEXT_INVALID.
        """
        emoji_map = self._load_map()
        ids = sorted(
            {
                str(v)
                for v in emoji_map.values()
                if not str(v).startswith(EMOJI_PLACEHOLDER_PREFIX)
            }
        )
        if not ids:
            return

        alt_map: dict[str, str] = {}
        for i in range(0, len(ids), GET_CUSTOM_EMOJI_STICKERS_BATCH_SIZE):
            batch = ids[i : i + GET_CUSTOM_EMOJI_STICKERS_BATCH_SIZE]
            try:
                stickers = await bot.get_custom_emoji_stickers(custom_emoji_ids=batch)
            except Exception:
                logger.exception("Не удалось получить custom emoji стикеры из Telegram")
                continue
            for sticker in stickers:
                if sticker.emoji:
                    alt_map[sticker.custom_emoji_id] = sticker.emoji

        missing = set(ids) - set(alt_map.keys())
        if missing:
            logger.warning(
                "Не найден alt-эмодзи для %d custom_emoji_id (возможно, ID удалены/неверны): %s",
                len(missing),
                ", ".join(sorted(missing)),
            )

        self._alt_emoji_map = alt_map
        logger.info("Синхронизировано %d alt-эмодзи для custom emoji", len(alt_map))

    def _load_map(self) -> dict[str, str]:
        if self._emoji_map is None:
            with open(self.emoji_map_path, encoding="utf-8") as f:
                raw = json.load(f)
            self._emoji_map = {
                k: v for k, v in raw.items() if not k.startswith("_")
            }
        return self._emoji_map

    def get_available_emojis(self) -> list[str]:
        return list(self._load_map().keys())

    def get_configured_count(self) -> tuple[int, int]:
        """Returns (configured, total)."""
        emoji_map = self._load_map()
        total = len(emoji_map)
        configured = sum(
            1 for v in emoji_map.values() if not v.startswith(EMOJI_PLACEHOLDER_PREFIX)
        )
        return configured, total

    def parse_text(self, raw_text: str) -> tuple[str, list[MessageEntity]]:
        """
        Replace {emoji_name} placeholders with placeholder char + entities.
        Falls back to regular unicode emoji or removes placeholder if not configured.
        """
        emoji_map = self._load_map()
        entities: list[MessageEntity] = []
        result_parts: list[str] = []
        last_end = 0

        for match in EMOJI_PATTERN.finditer(raw_text):
            result_parts.append(raw_text[last_end : match.start()])
            name = match.group(1).strip().lower()
            emoji_id = emoji_map.get(name) or emoji_map.get(match.group(1).strip())

            if emoji_id and not str(emoji_id).startswith(EMOJI_PLACEHOLDER_PREFIX):
                emoji_id = str(emoji_id)
                # Обязательно используем настоящий alt-эмодзи стикера, если он известен —
                # иначе Telegram может отклонить всё сообщение (ENTITY_TEXT_INVALID).
                wrap_char = self._alt_emoji_map.get(emoji_id, EMOJI_PLACEHOLDER_CHAR)
                offset = sum(_utf16_len(p) for p in result_parts)
                result_parts.append(wrap_char)
                entities.append(
                    MessageEntity(
                        type="custom_emoji",
                        offset=offset,
                        length=_utf16_len(wrap_char),
                        custom_emoji_id=emoji_id,
                    )
                )
            else:
                # Fallback: show name in brackets if emoji not configured
                fallback = f"[{name}]"
                result_parts.append(fallback)
                logger.debug("Emoji '%s' not configured, using fallback", name)

            last_end = match.end()

        result_parts.append(raw_text[last_end:])
        text = "".join(result_parts)
        return text, entities

    def preview_text(self, raw_text: str) -> str:
        """Preview without custom emoji IDs — for display in bot chat."""
        emoji_map = self._load_map()

        def replace(match: re.Match) -> str:
            name = match.group(1).strip()
            if name in emoji_map and not emoji_map[name].startswith(
                EMOJI_PLACEHOLDER_PREFIX
            ):
                return f"{EMOJI_PREVIEW_MARK}{name}{EMOJI_PREVIEW_MARK}"
            return f"[{name}]"

        return EMOJI_PATTERN.sub(replace, raw_text)

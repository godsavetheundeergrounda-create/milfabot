"""Milfyria Telegram bot entry point."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import Settings
from bot.constants import LOG_FORMAT
from bot.database.db import Database
from bot.handlers.router import setup_handlers
from bot.services.emoji import EmojiService
from bot.services.openrouter import OpenRouterClient
from bot.services.post_generator import PostGenerator
from bot.services.poster import PosterService
from bot.services.scheduler import PostScheduler

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = Settings.load()
    database = Database(settings.db_path)
    await database.init()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    openrouter = OpenRouterClient(
        api_key=settings.openrouter_api_key,
        models_config_path=settings.models_config_path,
        database=database,
    )
    post_generator = PostGenerator(
        openrouter=openrouter,
        system_prompt_path=settings.system_prompt_path,
        user_prompt_path=settings.user_prompt_path,
        database=database,
    )
    emoji_service = EmojiService(settings.emoji_map_path)
    await emoji_service.sync_alt_emojis(bot)
    poster = PosterService(
        bot=bot,
        database=database,
        post_generator=post_generator,
        emoji_service=emoji_service,
    )
    scheduler = PostScheduler(database=database, poster=poster)

    dp = Dispatcher()
    router = dp.router if hasattr(dp, "router") else None

    from aiogram import Router

    main_router = Router()
    setup_handlers(
        router=main_router,
        settings=settings,
        database=database,
        poster=poster,
        scheduler=scheduler,
        emoji_service=emoji_service,
    )
    dp.include_router(main_router)

    scheduler.start()
    await scheduler.schedule_all()

    logger.info("Milfyria bot started (owner_id=%s)", settings.owner_id)

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

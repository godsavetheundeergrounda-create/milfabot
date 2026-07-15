"""Random posting scheduler — 2 posts per day in time windows."""

import logging
import random
from datetime import datetime, time, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from bot.constants import (
    DEFAULT_EVENING_END,
    DEFAULT_EVENING_START,
    DEFAULT_MORNING_END,
    DEFAULT_MORNING_START,
    SCHEDULER_TIMEZONE,
    SCHEDULED_POST_LOG_PREVIEW_CHARS,
    SETTING_EVENING_END,
    SETTING_EVENING_START,
    SETTING_MORNING_END,
    SETTING_MORNING_START,
    SETTING_NEXT_EVENING_POST,
    SETTING_NEXT_MORNING_POST,
    SETTING_OWNER_ID,
)
from bot.database.db import Database
from bot.services.poster import PosterService

logger = logging.getLogger(__name__)


def _parse_time(value: str) -> time:
    parts = value.split(":")
    return time(int(parts[0]), int(parts[1]))


def _random_datetime_in_window(
    window_start: time, window_end: time, base_date: datetime | None = None
) -> datetime:
    base = base_date or datetime.now()
    start_dt = datetime.combine(base.date(), window_start)
    end_dt = datetime.combine(base.date(), window_end)

    if end_dt <= start_dt:
        end_dt += timedelta(days=1)

    now = datetime.now()
    if start_dt < now < end_dt:
        start_dt = now + timedelta(minutes=1)

    if start_dt >= end_dt:
        start_dt = datetime.combine(
            (base.date() + timedelta(days=1)), window_start
        )
        end_dt = datetime.combine(
            (base.date() + timedelta(days=1)), window_end
        )

    delta_seconds = int((end_dt - start_dt).total_seconds())
    if delta_seconds <= 0:
        delta_seconds = 60

    random_offset = random.randint(0, delta_seconds)
    return start_dt + timedelta(seconds=random_offset)


class PostScheduler:
    def __init__(self, database: Database, poster: PosterService):
        self.database = database
        self.poster = poster
        self.scheduler = AsyncIOScheduler(timezone=SCHEDULER_TIMEZONE)
        self._job_ids = ("morning_post", "evening_post")

    async def _get_window(self, period: str) -> tuple[time, time]:
        defaults = {
            "morning": (DEFAULT_MORNING_START, DEFAULT_MORNING_END),
            "evening": (DEFAULT_EVENING_START, DEFAULT_EVENING_END),
        }
        keys = {
            "morning": (SETTING_MORNING_START, SETTING_MORNING_END),
            "evening": (SETTING_EVENING_START, SETTING_EVENING_END),
        }
        start_default, end_default = defaults[period]
        start_key, end_key = keys[period]
        start = await self.database.get_setting(start_key, start_default)
        end = await self.database.get_setting(end_key, end_default)
        return _parse_time(start or start_default), _parse_time(end or end_default)

    async def _scheduled_post(self, period: str) -> None:
        if not await self.poster.is_enabled():
            logger.info("Posting disabled, skipping %s post", period)
            await self.schedule_period(period)
            return

        try:
            raw_text, model = await self.poster.generate_and_post(
                trigger_type=f"scheduled_{period}"
            )
            logger.info(
                "Scheduled %s post published (model=%s): %s...",
                period,
                model,
                raw_text[:SCHEDULED_POST_LOG_PREVIEW_CHARS],
            )
        except Exception as e:
            logger.exception("Failed scheduled %s post: %s", period, e)
            try:
                owner_id = await self.database.get_setting(SETTING_OWNER_ID)
                if owner_id:
                    await self.poster.bot.send_message(
                        int(owner_id),
                        f"⚠️ Ошибка автопоста ({period}): {e}",
                    )
            except Exception:
                pass

        await self.schedule_period(period)

    async def schedule_period(self, period: str) -> None:
        job_id = f"{period}_post"
        start, end = await self._get_window(period)
        run_at = _random_datetime_in_window(start, end)

        # If window already passed today, schedule for tomorrow
        if run_at <= datetime.now():
            tomorrow = datetime.now() + timedelta(days=1)
            run_at = _random_datetime_in_window(start, end, tomorrow)

        self.scheduler.add_job(
            self._scheduled_post,
            trigger=DateTrigger(run_date=run_at),
            args=[period],
            id=job_id,
            replace_existing=True,
        )
        next_key = (
            SETTING_NEXT_MORNING_POST
            if period == "morning"
            else SETTING_NEXT_EVENING_POST
        )
        await self.database.set_setting(next_key, run_at.isoformat())
        logger.info("Scheduled %s post at %s", period, run_at)

    async def schedule_all(self) -> None:
        await self.schedule_period("morning")
        await self.schedule_period("evening")

    async def get_next_posts_info(self) -> str:
        morning = await self.database.get_setting(
            SETTING_NEXT_MORNING_POST, "не задано"
        )
        evening = await self.database.get_setting(
            SETTING_NEXT_EVENING_POST, "не задано"
        )
        m_start, m_end = await self._get_window("morning")
        e_start, e_end = await self._get_window("evening")
        enabled = await self.poster.is_enabled()

        return (
            f"Статус: {'🟢 активен' if enabled else '🔴 пауза'}\n"
            f"Утро ({m_start.strftime('%H:%M')}–{m_end.strftime('%H:%M')}): {morning}\n"
            f"Вечер ({e_start.strftime('%H:%M')}–{e_end.strftime('%H:%M')}): {evening}"
        )

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    async def reschedule_all(self) -> None:
        await self.schedule_all()

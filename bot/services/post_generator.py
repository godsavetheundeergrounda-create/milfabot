"""Post generation service."""

import logging
import random
from pathlib import Path

from bot.constants import POST_ARTIFACT_PREFIX, POST_TOPICS
from bot.database.db import Database
from bot.services.openrouter import OpenRouterClient

logger = logging.getLogger(__name__)


class PostGenerator:
    def __init__(
        self,
        openrouter: OpenRouterClient,
        system_prompt_path: Path,
        user_prompt_path: Path,
        database: Database,
    ):
        self.openrouter = openrouter
        self.system_prompt_path = system_prompt_path
        self.user_prompt_path = user_prompt_path
        self.database = database
        self._system_prompt: str | None = None
        self._user_prompt_template: str | None = None

    def _load_system_prompt(self) -> str:
        if self._system_prompt is None:
            with open(self.system_prompt_path, encoding="utf-8") as f:
                self._system_prompt = f.read().strip()
        return self._system_prompt

    def _load_user_prompt_template(self) -> str:
        if self._user_prompt_template is None:
            with open(self.user_prompt_path, encoding="utf-8") as f:
                self._user_prompt_template = f.read().strip()
        return self._user_prompt_template

    def reload_prompt(self) -> None:
        self._system_prompt = None
        self._user_prompt_template = None

    async def generate_post(self, topic: str | None = None) -> tuple[str, str]:
        """Generate a post. Returns (post_text, model_used)."""
        if topic is None:
            topic = random.choice(POST_TOPICS)

        user_prompt = self._load_user_prompt_template().format(topic=topic)
        system_prompt = self._load_system_prompt()
        text, model = await self.openrouter.generate(system_prompt, user_prompt)

        # Clean up common LLM artifacts
        text = text.strip().strip('"').strip("«»")
        if text.startswith(POST_ARTIFACT_PREFIX):
            text = text[len(POST_ARTIFACT_PREFIX) :].strip()

        return text, model

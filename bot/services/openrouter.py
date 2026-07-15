"""OpenRouter API client with model fallback."""

import json
import logging
from pathlib import Path

import httpx

from bot.config import load_json
from bot.constants import (
    OPENROUTER_DEFAULT_FALLBACK_ERRORS,
    OPENROUTER_DEFAULT_MAX_TOKENS,
    OPENROUTER_DEFAULT_TEMPERATURE,
    OPENROUTER_ERROR_TEXT_LIMIT,
    OPENROUTER_HTTP_REFERER,
    OPENROUTER_TIMEOUT_SECONDS,
    OPENROUTER_URL,
    OPENROUTER_X_TITLE,
)
from bot.database.db import Database

logger = logging.getLogger(__name__)


class OpenRouterClient:
    def __init__(
        self,
        api_key: str,
        models_config_path: Path,
        database: Database,
    ):
        self.api_key = api_key
        self.models_config_path = models_config_path
        self.database = database
        self._config: dict | None = None

    def _get_config(self) -> dict:
        if self._config is None:
            self._config = load_json(self.models_config_path)
        return self._config

    def reload_config(self) -> None:
        self._config = None

    @property
    def models(self) -> list[str]:
        return self._get_config().get("models", [])

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[str, str]:
        """Generate text. Returns (text, model_used)."""
        config = self._get_config()
        models = config.get("models", [])
        fallback_codes = set(
            config.get("fallback_on_errors", OPENROUTER_DEFAULT_FALLBACK_ERRORS)
        )
        max_tokens = config.get("max_tokens", OPENROUTER_DEFAULT_MAX_TOKENS)
        temperature = config.get("temperature", OPENROUTER_DEFAULT_TEMPERATURE)

        if not models:
            raise RuntimeError("No models configured in config/models.json")

        last_error: Exception | None = None

        async with httpx.AsyncClient(timeout=OPENROUTER_TIMEOUT_SECONDS) as client:
            for model in models:
                try:
                    response = await client.post(
                        OPENROUTER_URL,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": OPENROUTER_HTTP_REFERER,
                            "X-Title": OPENROUTER_X_TITLE,
                        },
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                        },
                    )

                    if response.status_code in fallback_codes:
                        error_text = response.text[:OPENROUTER_ERROR_TEXT_LIMIT]
                        logger.warning(
                            "Model %s returned %s: %s",
                            model,
                            response.status_code,
                            error_text,
                        )
                        await self.database.log_model_usage(
                            model, False, f"HTTP {response.status_code}"
                        )
                        last_error = RuntimeError(
                            f"{model}: HTTP {response.status_code}"
                        )
                        continue

                    response.raise_for_status()
                    data = response.json()

                    content = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )

                    if not content:
                        await self.database.log_model_usage(
                            model, False, "Empty response"
                        )
                        last_error = RuntimeError(f"{model}: empty response")
                        continue

                    await self.database.log_model_usage(model, True)
                    logger.info("Generated post with model: %s", model)
                    return content, model

                except httpx.HTTPStatusError as e:
                    status = e.response.status_code
                    if status in fallback_codes:
                        await self.database.log_model_usage(
                            model, False, f"HTTP {status}"
                        )
                        last_error = e
                        logger.warning("Model %s failed: %s", model, e)
                        continue
                    await self.database.log_model_usage(model, False, str(e))
                    raise

                except (httpx.RequestError, json.JSONDecodeError) as e:
                    await self.database.log_model_usage(model, False, str(e))
                    last_error = e
                    logger.warning("Model %s request error: %s", model, e)
                    continue

        raise RuntimeError(
            f"All models failed. Last error: {last_error}"
        ) from last_error

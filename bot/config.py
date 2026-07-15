import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from bot.constants import (
    DEFAULT_DB_FILENAME,
    EMOJI_MAP_FILENAME,
    MODELS_CONFIG_FILENAME,
    SYSTEM_PROMPT_FILENAME,
    USER_PROMPT_FILENAME,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
PROMPTS_DIR = BASE_DIR / "prompts"
DATA_DIR = BASE_DIR / "data"


@dataclass
class Settings:
    bot_token: str
    owner_id: int
    openrouter_api_key: str
    db_path: Path
    models_config_path: Path
    emoji_map_path: Path
    system_prompt_path: Path
    user_prompt_path: Path

    @classmethod
    def load(cls) -> "Settings":
        bot_token = os.getenv("BOT_TOKEN", "")
        owner_id = int(os.getenv("OWNER_ID", "0"))
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        db_path = Path(os.getenv("DB_PATH", str(DATA_DIR / DEFAULT_DB_FILENAME)))

        if not bot_token:
            raise ValueError("BOT_TOKEN is required")
        if not owner_id:
            raise ValueError("OWNER_ID is required")
        if not openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is required")

        return cls(
            bot_token=bot_token,
            owner_id=owner_id,
            openrouter_api_key=openrouter_api_key,
            db_path=db_path,
            models_config_path=CONFIG_DIR / MODELS_CONFIG_FILENAME,
            emoji_map_path=CONFIG_DIR / EMOJI_MAP_FILENAME,
            system_prompt_path=PROMPTS_DIR / SYSTEM_PROMPT_FILENAME,
            user_prompt_path=PROMPTS_DIR / USER_PROMPT_FILENAME,
        )


def load_json(path: Path) -> dict | list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

import logging
import os
import sys
from pathlib import Path

from utils.resource_helper import get_resource_path, is_frozen

logger = logging.getLogger("bpm.secrets")

def load_env_file(dotenv_path: Path):
    """Simple parser for .env files to avoid external dependencies like python-dotenv."""
    if not dotenv_path.exists():
        return

    try:
        with open(dotenv_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
    except Exception as e:
        logger.warning(f"Error loading .env file from {dotenv_path}: {e}")

class SecretsLoader:
    _loaded = False

    @classmethod
    def get_discord_webhook_url(cls) -> str:
        if not cls._loaded:
            # 1. Try to load from the bundle (baked-in secret)
            # This works if .env is added to 'datas' in PyInstaller
            load_env_file(get_resource_path(".env"))

            # 2. Try to load from current directory (dev or portable mode)
            load_env_file(Path(".env"))

            # 3. Try to load from executable directory (external config mode)
            if is_frozen():
                load_env_file(Path(sys.executable).parent / ".env")

            cls._loaded = True

        return os.environ.get("DISCORD_WEBHOOK_URL", "")

    @classmethod
    def is_discord_available(cls) -> bool:
        return bool(cls.get_discord_webhook_url())

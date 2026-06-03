"""
Configuration module for Daily Insight Agent.

WHY THIS FILE EXISTS:
- Centralizes all environment variables and settings
- Makes the app configurable without changing code
- Enables different configs for dev/production

HOW IT RELATES TO AGENT THINKING:
- Agents need reliable access to config data (API keys, file paths)
- Central config is a pattern that prevents data leaks (no hardcoded secrets)
- Allows agents to know where to find data sources

HOW TO EXTEND:
- Add new settings here, then reference them in modules
- Add environment variable validation (e.g., check OPENAI_API_KEY is set)
- Create different config classes for dev/test/prod environments
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_env_path(name: str, default_path: Path) -> str:
    """Return an environment path, or the default if unset or blank."""
    value = os.getenv(name, "").strip()
    return value or str(default_path)


class Config:
    """Base configuration for Daily Insight Agent."""

    # ========== PATHS ==========
    # All paths relative to project root for portability
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    DIARY_DIR = DATA_DIR / "diary"
    WHATSAPP_DIR = DATA_DIR / "whatsapp_exports"
    GOALS_DIR = DATA_DIR / "goals"
    DAILY_INSIGHTS_DIR = DATA_DIR / "daily_insights"
    DB_PATH = DATA_DIR / "insights.db"

    # ========== OPENAI CONFIGURATION ==========
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-1-mini")

    # ========== DATA SOURCES ==========
    # OneDrive-synced paths (user-specific, set in .env)
    GOALS_FILE_PATH = get_env_path("GOALS_FILE_PATH", GOALS_DIR / "goals.txt")
    ONEDRIVE_DAILY_INSIGHTS_SHARE_URL = os.getenv(
        "ONEDRIVE_DAILY_INSIGHTS_SHARE_URL",
        "",
    )
    ONEDRIVE_DIARY_SHARE_URL = os.getenv(
        "ONEDRIVE_DIARY_SHARE_URL",
        "",
    )
    ONEDRIVE_DIARY2_SHARE_URL = os.getenv(
        "ONEDRIVE_DIARY2_SHARE_URL",
        "",
    )
    ONEDRIVE_DIARY_FILE_PATH = os.getenv(
        "ONEDRIVE_DIARY_FILE_PATH",
        "",
    )
    ONEDRIVE_WEEKLY_FILE_PATH = os.getenv(
        "ONEDRIVE_WEEKLY_FILE_PATH",
        "",
    )
    ONEDRIVE_DIARY_PATH = os.getenv(
        "ONEDRIVE_DIARY_PATH",
        "",
    )
    ONEDRIVE_DAILY_INSIGHTS_PATH = os.getenv(
        "ONEDRIVE_DAILY_INSIGHTS_PATH",
        "/MY LIFE/My Life Knowledge/AI_Thoughts",
    )
    ONEDRIVE_LINKEDIN_EXPORT_PATH = os.getenv(
        "ONEDRIVE_LINKEDIN_EXPORT_PATH",
        "",
    )
    ONEDRIVE_WHATSAPP_EXPORT_PATH = os.getenv(
        "ONEDRIVE_WHATSAPP_EXPORT_PATH",
        "",
    )
    RSS_SOURCES_FILE = DATA_DIR / "rss_sources.txt"

    # ========== AGENT CONFIGURATION ==========
    # How many recent diary entries to include in reflection
    DIARY_LOOKBACK_DAYS = int(os.getenv("DIARY_LOOKBACK_DAYS", 7))

    TELEGRAM_LOOKBACK_DAYS = int(os.getenv("TELEGRAM_LOOKBACK_DAYS", 30))
    TELEGRAM_CHANNELS = os.getenv("TELEGRAM_CHANNELS", "")
    TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "")
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_SESSION_STRING = os.getenv("TELEGRAM_SESSION_STRING", "")

    YOUTUBE_LOOKBACK_DAYS = int(os.getenv("YOUTUBE_LOOKBACK_DAYS", 14))
    YOUTUBE_CHANNEL_URLS = os.getenv("YOUTUBE_CHANNEL_URLS", "")
    YOUTUBE_WHISPER_ENABLED = os.getenv("YOUTUBE_WHISPER_ENABLED", "false").lower() == "true"
    YOUTUBE_WHISPER_MAX_MINUTES = int(os.getenv("YOUTUBE_WHISPER_MAX_MINUTES", 120))

    LINKEDIN_LOOKBACK_DAYS = int(os.getenv("LINKEDIN_LOOKBACK_DAYS", 14))
    WHATSAPP_LOOKBACK_DAYS = int(os.getenv("WHATSAPP_LOOKBACK_DAYS", 14))
    
    # Max tokens for API calls (keep cost reasonable)
    MAX_TOKENS_READER = int(os.getenv("MAX_TOKENS_READER", 1000))
    MAX_TOKENS_REFLECTION = int(os.getenv("MAX_TOKENS_REFLECTION", 1500))
    MAX_TOKENS_COACH = int(os.getenv("MAX_TOKENS_COACH", 800))

    # ========== FASTAPI CONFIGURATION ==========
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    def validate(self) -> bool:
        """
        Validate required configuration.
        
        SECURITY NOTE: If OPENAI_API_KEY is missing, the app will fail gracefully.
        This prevents accidental API calls with no credentials.
        """
        if not self.OPENAI_API_KEY:
            print("⚠️  WARNING: OPENAI_API_KEY not set in .env")
            return False
        return True

    def ensure_directories(self):
        """Create required directories if they don't exist."""
        for directory in [
            self.DIARY_DIR,
            self.WHATSAPP_DIR,
            self.GOALS_DIR,
            self.DAILY_INSIGHTS_DIR,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


# Create default config instance
config = Config()
config.ensure_directories()

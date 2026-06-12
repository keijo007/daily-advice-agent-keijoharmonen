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
    PERSONAL_DIR = DATA_DIR / "personal"
    PERSONAL_DIARY_DIR = PERSONAL_DIR / "diary"
    PERSONAL_GOALS_FILE = PERSONAL_DIR / "goals.md"
    PERSONAL_CURRENT_STATE_FILE = PERSONAL_DIR / "current_state.yaml"
    WHATSAPP_DIR = DATA_DIR / "whatsapp_exports"
    GOALS_DIR = DATA_DIR / "goals"
    DB_PATH = DATA_DIR / "insights.db"
    OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "daily_briefs"
    SOURCES_YAML = PROJECT_ROOT / "config" / "sources.yaml"
    SETTINGS_YAML = PROJECT_ROOT / "config" / "settings.yaml"

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
    ONEDRIVE_DAILY_INSIGHTS_PATH = os.getenv(
        "ONEDRIVE_DAILY_INSIGHTS_PATH",
        "",
    )
    UPLOAD_DAILY_INSIGHTS_TO_ONEDRIVE = os.getenv(
        "UPLOAD_DAILY_INSIGHTS_TO_ONEDRIVE",
        "false",
    ).lower() == "true"
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
    ONEDRIVE_GOALS_FILE_PATH = os.getenv(
        "ONEDRIVE_GOALS_FILE_PATH",
        "",
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

    # ========== EMAIL CONFIGURATION ==========
    GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
    GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
    GMAIL_REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN", "")
    GMAIL_LOOKBACK_DAYS = int(os.getenv("GMAIL_LOOKBACK_DAYS", 14))
    GMAIL_MESSAGE_LIMIT = int(os.getenv("GMAIL_MESSAGE_LIMIT", 10))
    GMAIL_QUERY = os.getenv("GMAIL_QUERY", "")

    OUTLOOK_CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID", "") or os.getenv("AZURE_CLIENT_ID", "")
    OUTLOOK_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET", "") or os.getenv("AZURE_CLIENT_SECRET", "")
    OUTLOOK_REFRESH_TOKEN = os.getenv("OUTLOOK_REFRESH_TOKEN", "") or os.getenv("ONEDRIVE_REFRESH_TOKEN", "")
    OUTLOOK_TENANT_ID = os.getenv("OUTLOOK_TENANT_ID", "") or os.getenv("AZURE_TENANT_ID", "")
    OUTLOOK_LOOKBACK_DAYS = int(os.getenv("OUTLOOK_LOOKBACK_DAYS", 14))
    OUTLOOK_MESSAGE_LIMIT = int(os.getenv("OUTLOOK_MESSAGE_LIMIT", 10))

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
    PREVIOUS_INSIGHTS_LIMIT = int(os.getenv("PREVIOUS_INSIGHTS_LIMIT", 15))
    
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
            self.PERSONAL_DIARY_DIR,
            self.WHATSAPP_DIR,
            self.GOALS_DIR,
            self.OUTPUTS_DIR,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


# Create default config instance
config = Config()
config.ensure_directories()

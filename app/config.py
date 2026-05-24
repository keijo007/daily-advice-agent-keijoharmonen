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
    GOALS_FILE_PATH = os.getenv("GOALS_FILE_PATH", str(GOALS_DIR / "goals.txt"))
    RSS_SOURCES_FILE = DATA_DIR / "rss_sources.txt"

    # ========== AGENT CONFIGURATION ==========
    # How many recent diary entries to include in reflection
    DIARY_LOOKBACK_DAYS = int(os.getenv("DIARY_LOOKBACK_DAYS", 7))
    
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

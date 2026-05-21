"""
Daily Insight Agent - Your personal AI coach.

A Python-based AI agent that reads from multiple sources (diary, RSS, WhatsApp exports, 
goals, etc.), analyzes thinking patterns, identifies cognitive biases, and provides 
personalized, actionable daily advice.

CORE COMPONENTS:
- Collectors: Read from different data sources
- Services: Normalize, deduplicate, store data
- Agents: AI reasoning (Reader, Reflection, Coach)
- Pipeline: Orchestrate the workflow
- Web UI: Display results via FastAPI

USAGE:
    from app.services.daily_pipeline import run_daily_pipeline
    insight = run_daily_pipeline()
    print(insight.practical_tip)

Or start the web server:
    python -m uvicorn app.main:app --reload
    # Open http://localhost:8000

ARCHITECTURE:
    Data Sources → Collectors → Normalize → Deduplicate → Storage
                                                              ↓
                                                        Daily Pipeline
                                                              ↓
                          Reader Agent → Reflection Agent → Coach Agent
                                                              ↓
                                                        DailyInsight
                                                              ↓
                                                    Web UI (FastAPI)

PRIVACY:
    - API keys stored in .env (never in code)
    - Data stored locally in SQLite
    - Limited diary sent to OpenAI
    - No cloud sync by default
"""

__version__ = "1.0.0"
__author__ = "AI Development"
__description__ = "Personal AI coach providing daily insights"

# Import key components for convenience
from app.config import config
from app.models import ContentItem, DailyInsight, SourceType
from app.services.daily_pipeline import run_daily_pipeline

__all__ = [
    "config",
    "ContentItem",
    "DailyInsight",
    "SourceType",
    "run_daily_pipeline",
]

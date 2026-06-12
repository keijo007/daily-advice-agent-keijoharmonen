"""Personal Signal OS package exports."""

__version__ = "1.0.0"
__author__ = "AI Development"
__description__ = "Personal Signal OS - daily intelligence brief"

# Import key components for convenience
from app.config import config
from app.models import ContentItem, DailyInsight, SourceType


def run_daily_pipeline():
    """Backward-compatible lazy entrypoint for daily run."""
    from app.services.daily_pipeline import DailyPipeline

    return DailyPipeline().run_daily()

__all__ = [
    "config",
    "ContentItem",
    "DailyInsight",
    "SourceType",
    "run_daily_pipeline",
]

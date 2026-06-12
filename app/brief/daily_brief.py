"""Daily brief builder helper."""

from app.services.daily_pipeline import DailyPipeline


class DailyBriefBuilder:
    """Build a full daily brief with one call."""

    def build(self):
        return DailyPipeline().run_daily()

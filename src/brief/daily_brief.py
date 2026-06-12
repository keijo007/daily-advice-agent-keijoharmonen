"""Daily brief builder adapter."""

from app.services.daily_pipeline import DailyPipeline


class DailyBriefBuilder:
    """Build daily brief via Signal OS pipeline."""

    def build(self):
        return DailyPipeline().run_daily()

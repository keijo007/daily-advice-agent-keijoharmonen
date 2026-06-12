"""Daily brief builder helper."""


class DailyBriefBuilder:
    """Build a full daily brief with one call."""

    def build(self):
        from app.services.daily_pipeline import DailyPipeline

        return DailyPipeline().run_daily()

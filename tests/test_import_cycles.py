"""Regression tests for import cycle safety."""


def test_import_daily_pipeline_and_brief_builder_without_cycle():
    """Importing key modules must not trigger circular import errors."""
    from app.services.daily_pipeline import DailyPipeline, run_daily_pipeline
    from app.brief.daily_brief import DailyBriefBuilder

    assert DailyPipeline is not None
    assert run_daily_pipeline is not None
    assert DailyBriefBuilder is not None


def test_app_package_exposes_lazy_run_daily_pipeline():
    """`app.run_daily_pipeline` should be available and lazily resolved."""
    import app

    assert hasattr(app, "run_daily_pipeline")
    assert callable(app.run_daily_pipeline)

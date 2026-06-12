"""Collector tests."""

from pathlib import Path
from tempfile import TemporaryDirectory

from app.collectors.diary_collector import DiaryCollector
from app.collectors.goals_collector import GoalsCollector
from app.models import SourceType


def test_diary_collector_reads_markdown_files():
    with TemporaryDirectory() as tmpdir:
        diary_dir = Path(tmpdir)
        (diary_dir / "2024-01-15.md").write_text("# My Day\nToday was productive.", encoding="utf-8")

        items = DiaryCollector(diary_dir).collect()

        assert len(items) == 1
        assert items[0].source == SourceType.DIARY
        assert "productive" in items[0].content


def test_diary_collector_ignores_non_markdown_text():
    with TemporaryDirectory() as tmpdir:
        diary_dir = Path(tmpdir)
        (diary_dir / "note.md").write_text("Markdown note", encoding="utf-8")
        (diary_dir / "data.json").write_text('{"data":"value"}', encoding="utf-8")

        items = DiaryCollector(diary_dir).collect()

        assert len(items) == 1
        assert items[0].title == "note"


def test_goals_collector_reads_file():
    with TemporaryDirectory() as tmpdir:
        goals_path = Path(tmpdir) / "goals.txt"
        goals_path.write_text("1. Learn Python\n2. Build AI agent", encoding="utf-8")

        items = GoalsCollector(str(goals_path)).collect()

        assert len(items) == 1
        assert items[0].source == SourceType.GOALS

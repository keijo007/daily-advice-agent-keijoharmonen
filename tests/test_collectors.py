"""
Tests for collectors.

WHY TESTS MATTER:
- Ensure data is collected correctly
- Prevent regressions when code changes
- Document how components work
- Make refactoring safe

HOW TO RUN:
  pytest tests/test_collectors.py
  pytest tests/test_collectors.py -v  # verbose
  pytest tests/test_collectors.py::test_diary_collector  # single test

EDUCATIONAL VALUE:
- Shows how to test file I/O
- Demonstrates mocking and fixtures
- Examples of assertion patterns
"""

import pytest
from pathlib import Path
from datetime import datetime
from tempfile import TemporaryDirectory

from app.collectors.diary_collector import DiaryCollector
from app.collectors.goals_collector import GoalsCollector
from app.models import SourceType


class TestDiaryCollector:
    """Test diary file collection."""
    
    def test_collects_diary_files(self):
        \"\"\"
        Test that diary collector finds and reads .md and .txt files.
        
        This demonstrates:
        - Creating temporary files for testing
        - Verifying correct parsing
        - Checking ContentItem structure
        \"\"\"
        
        # Create temp directory with test files
        with TemporaryDirectory() as tmpdir:
            diary_dir = Path(tmpdir)
            
            # Create test diary file
            diary_file = diary_dir / "2024-01-15.md"
            diary_file.write_text("# My Day\\nToday was productive.", encoding="utf-8")
            
            # Collect
            collector = DiaryCollector(diary_dir)
            items = collector.collect()
            
            # Verify
            assert len(items) == 1, "Should find one diary file"
            assert items[0].source == SourceType.DIARY
            assert items[0].author == "You"
            assert "productive" in items[0].content
            print("✓ Diary collector works!")
    
    def test_empty_directory(self):
        \"\"\"Test that empty directory returns empty list.\"\"\"
        
        with TemporaryDirectory() as tmpdir:
            collector = DiaryCollector(Path(tmpdir))
            items = collector.collect()
            
            assert len(items) == 0
            print("✓ Empty directory handled correctly!")
    
    def test_skips_non_text_files(self):
        \"\"\"Test that non-.md/.txt files are ignored.\"\"\"
        
        with TemporaryDirectory() as tmpdir:
            diary_dir = Path(tmpdir)
            
            # Create various files
            (diary_dir / "note.md").write_text("Markdown note")
            (diary_dir / "data.json").write_text('{"data": "value"}')
            (diary_dir / "image.png").write_text("fake png")
            
            # Collect
            collector = DiaryCollector(diary_dir)
            items = collector.collect()
            
            # Only .md file should be collected
            assert len(items) == 1
            assert items[0].title == "note"
            print("✓ Non-text files correctly skipped!")


class TestGoalsCollector:
    \"\"\"Test goals file collection.\"\"\"
    
    def test_collects_goals(self):
        \"\"\"Test that goals are read from file.\"\"\"
        
        with TemporaryDirectory() as tmpdir:
            goals_path = Path(tmpdir) / "goals.txt"
            goals_content = \"\"\"1. Learn Python\\n2. Build an AI agent\\n3. Deploy to cloud\"\"\"
            goals_path.write_text(goals_content, encoding="utf-8")
            
            # Collect
            collector = GoalsCollector(str(goals_path))
            items = collector.collect()
            
            # Verify
            assert len(items) == 1
            assert items[0].source == SourceType.GOALS
            assert "Learn Python" in items[0].content
            print("✓ Goals collector works!")
    
    def test_missing_goals_file(self):
        \"\"\"Test that missing file returns empty list.\"\"\"
        
        collector = GoalsCollector("/nonexistent/path/goals.txt")
        items = collector.collect()
        
        assert len(items) == 0
        print("✓ Missing file handled gracefully!")


# Run tests with: pytest tests/test_collectors.py

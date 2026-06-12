#!/usr/bin/env python3
"""
Safe runner for Personal Signal OS.

Creates missing local directories/files and runs markdown brief generation.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.daily_pipeline import DailyPipeline


def ensure_local_files(root: Path):
    personal = root / "data" / "personal"
    diary = personal / "diary"
    outputs = root / "outputs" / "daily_briefs"

    diary.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)

    goals = personal / "goals.md"
    if not goals.exists():
        goals.write_text(
            "# Goals\n\n## current_focus\n- Build Personal Signal OS\n",
            encoding="utf-8",
        )

    state = personal / "current_state.yaml"
    if not state.exists():
        state.write_text(
            "current_focus:\n  - Build Personal Signal OS\n\navoid:\n  - hype without evidence\n",
            encoding="utf-8",
        )

    today_diary = diary / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    if not today_diary.exists():
        today_diary.write_text(
            "# Daily note\n\nCaptured initial state for Personal Signal OS run.\n",
            encoding="utf-8",
        )


def main() -> int:
    root = Path(__file__).parent.parent
    ensure_local_files(root)

    pipeline = DailyPipeline()
    brief = pipeline.run_daily()
    if not brief:
        print("✗ Failed to generate daily brief")
        return 1

    print(f"✓ Safe run complete for {brief.date}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

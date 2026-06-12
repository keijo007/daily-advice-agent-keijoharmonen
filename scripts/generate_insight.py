"""
Generate Personal Signal OS daily brief (markdown-only).

Usage:
    python scripts/generate_insight.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.daily_pipeline import DailyPipeline


def main() -> int:
    pipeline = DailyPipeline()
    brief = pipeline.run_daily()
    if not brief:
        print("✗ Daily brief generation failed")
        return 1

    print(f"✓ Daily brief generated for {brief.date}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

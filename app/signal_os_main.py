"""
Personal Signal OS CLI entrypoint.

Commands:
- collect
- score
- brief
- run-daily
- feedback
"""

from __future__ import annotations

import argparse
from datetime import datetime

from app.feedback.feedback_store import FeedbackStore
from app.models import Feedback
from app.services.daily_pipeline import DailyPipeline


def run_collect(_: argparse.Namespace):
    pipeline = DailyPipeline()
    raw = pipeline.collect()
    normalized = pipeline.normalize_and_store(raw)
    print(f"✓ Collected {len(raw)} items, stored {len(normalized)} after dedupe")


def run_score(_: argparse.Namespace):
    pipeline = DailyPipeline()
    goals, current_state, _ = pipeline._load_personal_context()
    items = pipeline.storage.get_items_since(lookback_days=2)
    scored = pipeline.score(items, goals, current_state)

    buckets = {}
    for item in scored:
        buckets[item.signal_type.value] = buckets.get(item.signal_type.value, 0) + 1

    print("✓ Scoring completed")
    for key in sorted(buckets):
        print(f"  - {key}: {buckets[key]}")


def run_brief(_: argparse.Namespace):
    pipeline = DailyPipeline()
    goals, current_state, recent_diary = pipeline._load_personal_context()
    items = pipeline.storage.get_items_since(lookback_days=2)
    scored = pipeline.score(items, goals, current_state)
    brief, output_path = pipeline.generate_brief(scored, goals, current_state, recent_diary)
    print(f"✓ Brief generated: {output_path}")
    print(f"  Signals: {len(brief.top_signals)} | Opportunities: {len(brief.opportunities)}")


def run_daily(_: argparse.Namespace):
    pipeline = DailyPipeline()
    brief = pipeline.run_daily()
    if brief:
        print(f"✓ Daily run complete for {brief.date}")


def run_feedback(args: argparse.Namespace):
    feedback = Feedback(
        date=datetime.now().strftime("%Y-%m-%d"),
        item_id=args.item_id,
        rating=args.rating,
        note=args.note,
    )
    saved = FeedbackStore().save_feedback(feedback)
    if saved:
        print(f"✓ Feedback saved for {args.item_id}")
    else:
        print("✗ Failed to save feedback")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Personal Signal OS")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("collect", help="Collect and normalize items")
    sub.add_parser("score", help="Score existing items")
    sub.add_parser("brief", help="Generate daily markdown brief")
    sub.add_parser("run-daily", help="Collect -> score -> brief")

    fb = sub.add_parser("feedback", help="Store feedback for an item")
    fb.add_argument("--item-id", required=True)
    fb.add_argument("--rating", required=True, choices=["+", "-", "?", "!"])
    fb.add_argument("--note", default=None)

    return parser


def main():
    args = build_parser().parse_args()

    handlers = {
        "collect": run_collect,
        "score": run_score,
        "brief": run_brief,
        "run-daily": run_daily,
        "feedback": run_feedback,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()

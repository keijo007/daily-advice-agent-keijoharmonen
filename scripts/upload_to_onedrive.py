"""
Upload the generated Personal Signal OS markdown brief to OneDrive.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import config
from app.services.daily_pipeline import DailyPipeline
from app.services.onedrive_client import OneDriveClient


def _load_or_generate_markdown(today: str) -> str:
    brief_path = Path("outputs") / "daily_briefs" / f"{today}.md"
    if brief_path.exists():
        return brief_path.read_text(encoding="utf-8")

    pipeline = DailyPipeline()
    brief = pipeline.run_daily()
    if not brief:
        raise RuntimeError("Pipeline failed, no brief generated")

    if not brief_path.exists():
        raise RuntimeError(f"Expected brief file not found: {brief_path}")

    return brief_path.read_text(encoding="utf-8")


def upload_to_onedrive():
    print("\n📤 UPLOADING DAILY BRIEF TO ONEDRIVE")
    print("-" * 45)

    client = OneDriveClient()
    if not client.enabled:
        print("⚠️  OneDrive not configured, skipping upload")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    markdown = _load_or_generate_markdown(today)

    if config.ONEDRIVE_DAILY_INSIGHTS_SHARE_URL:
        print("ℹ️  Uploading via shared folder URL")
        ok = client.upload_to_shared_folder(
            config.ONEDRIVE_DAILY_INSIGHTS_SHARE_URL,
            f"{today}.md",
            markdown,
        )
    else:
        base = (config.ONEDRIVE_DAILY_INSIGHTS_PATH or "DailyInsights").rstrip("/")
        remote_path = f"{base}/{today}.md"
        print(f"ℹ️  Uploading to OneDrive path: {remote_path}")
        ok = client.write_file(remote_path, markdown)

    if ok:
        print(f"✓ Uploaded {today}.md")
    else:
        print("✗ Upload failed")


if __name__ == "__main__":
    upload_to_onedrive()

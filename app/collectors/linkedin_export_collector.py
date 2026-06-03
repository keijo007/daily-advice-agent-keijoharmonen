"""
LinkedIn Export Collector - reads LinkedIn data export files.

Reads CSV files from a configured OneDrive folder and extracts recent updates.
"""

import csv
from datetime import datetime, timedelta
from typing import List, Optional
from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceType
from app.config import config
from app.services.onedrive_client import OneDriveClient


class LinkedInExportCollector(BaseCollector):
    """Collects LinkedIn updates from exported CSV files."""

    def __init__(self):
        super().__init__(SourceType.LINKEDIN)

    def collect(self) -> List[ContentItem]:
        items: List[ContentItem] = []

        if not config.ONEDRIVE_LINKEDIN_EXPORT_PATH:
            print("ℹ️  LinkedIn export path not set")
            return items

        client = OneDriveClient()
        if not client.enabled:
            print("ℹ️  OneDrive not configured for LinkedIn export")
            return items

        files = client.list_files(config.ONEDRIVE_LINKEDIN_EXPORT_PATH)
        if not files:
            print("⚠️  No LinkedIn export files found")
            return items

        csv_files = [f for f in files if f.lower().endswith(".csv")]
        if not csv_files:
            print("⚠️  No LinkedIn CSV files found")
            return items

        since = datetime.now() - timedelta(days=config.LINKEDIN_LOOKBACK_DAYS)

        for filename in csv_files:
            content = client.read_file(f"{config.ONEDRIVE_LINKEDIN_EXPORT_PATH}/{filename}")
            if not content:
                continue

            items.extend(self._parse_csv(filename, content, since))

        return items

    def _parse_csv(self, filename: str, content: str, since: datetime) -> List[ContentItem]:
        items: List[ContentItem] = []
        reader = csv.DictReader(content.splitlines())

        for row in reader:
            text = self._extract_text(row)
            if not text:
                continue

            timestamp = self._extract_timestamp(row) or datetime.now()
            if timestamp < since:
                continue

            item = self._create_item(
                title=f"LinkedIn: {filename}",
                content=text,
                author="LinkedIn",
                timestamp=timestamp,
                raw_path=f"onedrive:{config.ONEDRIVE_LINKEDIN_EXPORT_PATH}/{filename}",
            )
            items.append(item)

        if items:
            print(f"🔗 Loaded {len(items)} LinkedIn items from {filename}")
        return items

    @staticmethod
    def _extract_text(row: dict) -> Optional[str]:
        candidates = [
            "ShareCommentary",
            "Commentary",
            "Text",
            "PostText",
            "UpdateText",
            "Content",
        ]
        for key in candidates:
            value = row.get(key)
            if value:
                return str(value).strip()
        return None

    @staticmethod
    def _extract_timestamp(row: dict) -> Optional[datetime]:
        candidates = [
            "Date",
            "Time",
            "Created",
            "Timestamp",
            "Created At",
        ]
        for key in candidates:
            value = row.get(key)
            if value:
                try:
                    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                except Exception:
                    continue
        return None

"""Collect Outlook emails via Microsoft Graph API."""

from datetime import datetime, timedelta
from typing import List
from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceType
from app.config import config
from app.services.onedrive_client import OneDriveClient


class OutlookCollector(BaseCollector):
    """Collects recent Outlook messages from Microsoft Graph."""

    def __init__(self):
        super().__init__(SourceType.OUTLOOK)

    def collect(self) -> List[ContentItem]:
        items: List[ContentItem] = []

        client = OneDriveClient()
        if not client.enabled:
            print("ℹ️  Outlook/Microsoft Graph credentials not configured")
            return items

        since = datetime.now() - timedelta(days=config.OUTLOOK_LOOKBACK_DAYS)
        since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")
        messages = client.read_mail_messages(
            folder="Inbox",
            limit=config.OUTLOOK_MESSAGE_LIMIT,
            since=since_str,
        )

        if not messages:
            print("ℹ️  No Outlook messages found")
            return items

        for msg in messages:
            subject = msg.get("subject", "Outlook message")
            sender = "Outlook"
            sender_info = msg.get("from", {}).get("emailAddress", {})
            if isinstance(sender_info, dict):
                sender = sender_info.get("name") or sender_info.get("address") or sender

            preview = msg.get("bodyPreview", "")
            timestamp = datetime.now()
            received = msg.get("receivedDateTime")
            if received:
                try:
                    timestamp = datetime.fromisoformat(received.replace("Z", "+00:00"))
                except Exception:
                    pass

            item = self._create_item(
                title=f"Outlook: {subject}",
                content=f"From: {sender}\n\n{preview}",
                author=sender,
                timestamp=timestamp,
                raw_path=f"outlook:{msg.get('id', '')}",
            )
            items.append(item)

        if items:
            print(f"📧 Loaded {len(items)} Outlook items")
        return items

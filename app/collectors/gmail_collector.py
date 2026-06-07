"""Collect Gmail messages using the Gmail REST API."""

from datetime import datetime
from typing import List
from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceType
from app.config import config
from app.services.gmail_client import GmailClient


class GmailCollector(BaseCollector):
    """Collects recent Gmail messages for analysis."""

    def __init__(self):
        super().__init__(SourceType.GMAIL)

    def collect(self) -> List[ContentItem]:
        items: List[ContentItem] = []

        client = GmailClient()
        if not client.enabled:
            print("ℹ️  Gmail credentials not configured")
            return items

        query = config.GMAIL_QUERY or f"newer_than:{config.GMAIL_LOOKBACK_DAYS}d"
        messages = client.list_messages(query=query, max_results=config.GMAIL_MESSAGE_LIMIT)

        if not messages:
            print("ℹ️  No Gmail messages found")
            return items

        for msg in messages:
            message_id = msg.get("id")
            if not message_id:
                continue

            detail = client.get_message(message_id)
            if not detail:
                continue

            title = client.extract_subject(detail) or "Gmail message"
            snippet = client.extract_snippet(detail) or msg.get("snippet", "")
            sender = client.extract_sender(detail)
            timestamp = datetime.now()

            item = self._create_item(
                title=f"Gmail: {title}",
                content=f"From: {sender}\n\n{snippet}",
                author=sender,
                timestamp=timestamp,
                raw_path=f"gmail:{message_id}",
            )
            items.append(item)

        if items:
            print(f"✉️  Loaded {len(items)} Gmail items")
        return items

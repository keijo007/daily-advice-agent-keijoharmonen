"""Collector adapters."""

from app.collectors.rss_collector import RSSCollector
from app.collectors.local_markdown_collector import LocalMarkdownCollector
from app.collectors.email_collector_stub import GmailCollectorStub, OutlookCollectorStub
from app.collectors.telegram_collector_stub import TelegramCollectorStub
from app.collectors.calendar_collector_stub import CalendarCollectorStub
from app.collectors.youtube_collector_stub import YouTubeCollectorStub

__all__ = [
    "RSSCollector",
    "LocalMarkdownCollector",
    "GmailCollectorStub",
    "OutlookCollectorStub",
    "TelegramCollectorStub",
    "CalendarCollectorStub",
    "YouTubeCollectorStub",
]

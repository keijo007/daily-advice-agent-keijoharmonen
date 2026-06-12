"""
Collectors package - data input layer for Daily Insight Agent.

All collectors follow the same pattern:
1. Inherit from BaseCollector
2. Implement collect() → List[ContentItem]
3. Return normalized, standardized data

This makes it easy to add new sources without changing agent logic.
"""

from app.collectors.base_collector import BaseCollector
from app.collectors.rss_collector import RSSCollector
from app.collectors.local_markdown_collector import LocalMarkdownCollector
from app.collectors.email_collector_stub import GmailCollectorStub, OutlookCollectorStub
from app.collectors.telegram_collector_stub import TelegramCollectorStub
from app.collectors.calendar_collector_stub import CalendarCollectorStub
from app.collectors.youtube_collector_stub import YouTubeCollectorStub

# Legacy collectors kept for compatibility; Signal OS pipeline does not use them by default.
from app.collectors.diary_collector import DiaryCollector
from app.collectors.whatsapp_export_collector import WhatsAppCollector
from app.collectors.goals_collector import GoalsCollector
from app.collectors.youtube_collector import YouTubeCollector
from app.collectors.telegram_collector import TelegramCollector
from app.collectors.linkedin_export_collector import LinkedInExportCollector
from app.collectors.gmail_collector import GmailCollector
from app.collectors.outlook_collector import OutlookCollector

__all__ = [
    "BaseCollector",
    "LocalMarkdownCollector",
    "GmailCollectorStub",
    "OutlookCollectorStub",
    "TelegramCollectorStub",
    "CalendarCollectorStub",
    "YouTubeCollectorStub",
    "DiaryCollector",
    "WhatsAppCollector",
    "RSSCollector",
    "GoalsCollector",
    "YouTubeCollector",
    "TelegramCollector",
    "LinkedInExportCollector",
    "GmailCollector",
    "OutlookCollector",
]

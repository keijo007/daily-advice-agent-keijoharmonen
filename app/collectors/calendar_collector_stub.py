"""
Calendar collector stub for Personal Signal OS.

Use official calendar APIs only:
- Google Calendar API
- Microsoft Graph Calendar API
"""

from __future__ import annotations

from typing import List

from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceType


class CalendarCollectorStub(BaseCollector):
    """Stub for future calendar integration."""

    def __init__(self):
        super().__init__(SourceType.PERSONAL)

    def collect(self) -> List[ContentItem]:
        # TODO: Integrate Google Calendar and/or Outlook Calendar via official APIs.
        # TODO: Model event deadlines as ContentItem.deadline for urgency scoring.
        return []

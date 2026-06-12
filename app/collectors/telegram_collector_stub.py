"""
Telegram collector stub for Personal Signal OS.

Use official Telegram APIs only.
"""

from __future__ import annotations

from typing import List

from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceType


class TelegramCollectorStub(BaseCollector):
    """Stub for future Telegram integration."""

    def __init__(self):
        super().__init__(SourceType.TELEGRAM)

    def collect(self) -> List[ContentItem]:
        # TODO: Implement Telegram client integration using TELEGRAM_API_ID/HASH from env.
        # TODO: Add configurable channel list and lookback window.
        return []

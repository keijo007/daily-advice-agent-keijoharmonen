"""
YouTube collector stub for Personal Signal OS.

Use official YouTube Data API and optional transcript APIs.
"""

from __future__ import annotations

from typing import List

from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceType


class YouTubeCollectorStub(BaseCollector):
    """Stub for future YouTube integration."""

    def __init__(self):
        super().__init__(SourceType.YOUTUBE)

    def collect(self) -> List[ContentItem]:
        # TODO: Integrate YouTube Data API with channel/watch-history sources.
        # TODO: Optionally fetch captions/transcripts via official-supported methods.
        return []

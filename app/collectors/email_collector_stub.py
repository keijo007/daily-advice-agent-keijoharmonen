"""
Email collector stubs for Personal Signal OS.

These stubs intentionally do not require credentials yet.
Use official APIs only when integrating:
- Gmail API (google-api-python-client)
- Microsoft Graph API (Outlook)
"""

from __future__ import annotations

from typing import List

from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceBias, SourceType


class GmailCollectorStub(BaseCollector):
    """Stub for future Gmail API integration."""

    def __init__(self):
        super().__init__(SourceType.GMAIL)

    def collect(self) -> List[ContentItem]:
        # TODO: Implement Gmail API integration using OAuth2.
        # TODO: Read credentials from environment variables, never hardcode secrets.
        return []


class OutlookCollectorStub(BaseCollector):
    """Stub for future Outlook/Microsoft Graph integration."""

    def __init__(self):
        super().__init__(SourceType.OUTLOOK)

    def collect(self) -> List[ContentItem]:
        # TODO: Implement Microsoft Graph messages integration.
        # TODO: Use AZURE_CLIENT_ID/AZURE_CLIENT_SECRET/AZURE_TENANT_ID from env.
        return []

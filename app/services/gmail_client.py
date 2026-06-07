"""Gmail API client helper for Daily Insight Agent.

This module uses OAuth2 refresh tokens to obtain Gmail access tokens and read
recent messages. It is intentionally lightweight and uses only requests.
"""

import os
from typing import List, Optional


class GmailClient:
    """Lightweight Gmail REST API client."""

    TOKEN_URL = "https://oauth2.googleapis.com/token"
    MESSAGES_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
    MESSAGE_FORMAT_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}"

    def __init__(self):
        self.client_id = os.getenv("GMAIL_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("GMAIL_CLIENT_SECRET", "").strip()
        self.refresh_token = os.getenv("GMAIL_REFRESH_TOKEN", "").strip()
        self.enabled = bool(self.client_id and self.client_secret and self.refresh_token)
        self.access_token = ""

    def _get_access_token(self) -> Optional[str]:
        if self.access_token:
            return self.access_token

        if not self.enabled:
            return None

        try:
            import requests

            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            }
            response = requests.post(self.TOKEN_URL, data=payload, timeout=20)
            if response.status_code != 200:
                return None

            data = response.json()
            self.access_token = data.get("access_token", "")
            return self.access_token

        except Exception:
            return None

    def list_messages(self, query: str = "", max_results: int = 10) -> List[dict]:
        access_token = self._get_access_token()
        if not access_token:
            return []

        try:
            import requests

            params = {
                "maxResults": max_results,
            }
            if query:
                params["q"] = query

            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(self.MESSAGES_URL, headers=headers, params=params, timeout=20)
            if response.status_code != 200:
                return []

            return response.json().get("messages", [])
        except Exception:
            return []

    def get_message(self, message_id: str) -> Optional[dict]:
        access_token = self._get_access_token()
        if not access_token:
            return None

        try:
            import requests

            url = self.MESSAGE_FORMAT_URL.format(message_id=message_id)
            params = {
                "format": "metadata",
                "metadataHeaders": ["Subject", "From", "Date"],
            }
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(url, headers=headers, params=params, timeout=20)
            if response.status_code != 200:
                return None

            return response.json()
        except Exception:
            return None

    @staticmethod
    def extract_snippet(message: dict) -> str:
        return message.get("snippet", "") if isinstance(message, dict) else ""

    @staticmethod
    def extract_subject(message: dict) -> str:
        payload = message.get("payload", {}) if isinstance(message, dict) else {}
        headers = payload.get("headers", [])
        for header in headers:
            if header.get("name", "").lower() == "subject":
                return header.get("value", "")
        return "Email"

    @staticmethod
    def extract_sender(message: dict) -> str:
        payload = message.get("payload", {}) if isinstance(message, dict) else {}
        headers = payload.get("headers", [])
        for header in headers:
            if header.get("name", "").lower() == "from":
                return header.get("value", "")
        return "Gmail"

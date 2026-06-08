"""
Telegram Collector - fetches recent messages from Telegram channels.

Requires Telethon user session (TELEGRAM_SESSION_STRING).
"""

import re
from datetime import datetime, timedelta
from typing import List
from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceType
from app.config import config


class TelegramCollector(BaseCollector):
    """Telegram message collector using Telethon user session."""

    def __init__(self):
        super().__init__(SourceType.TELEGRAM)

    def collect(self) -> List[ContentItem]:
        if not (config.TELEGRAM_API_ID and config.TELEGRAM_API_HASH):
            print("ℹ️  Telegram API credentials not set")
            return []
        if not config.TELEGRAM_SESSION_STRING:
            print("ℹ️  TELEGRAM_SESSION_STRING not set")
            return []

        channels = self._parse_channels(config.TELEGRAM_CHANNELS)
        if not channels:
            print("ℹ️  No Telegram channels configured")
            return []

        try:
            from telethon import TelegramClient
            from telethon.sessions import StringSession
        except Exception as e:
            print(f"ℹ️  Telethon not installed: {e}")
            return []

        since = datetime.now() - timedelta(days=config.TELEGRAM_LOOKBACK_DAYS)
        items: List[ContentItem] = []

        with TelegramClient(
            StringSession(config.TELEGRAM_SESSION_STRING),
            int(config.TELEGRAM_API_ID),
            config.TELEGRAM_API_HASH,
        ) as client:
            for channel in channels:
                try:
                    messages = []
                    async_iter = client.iter_messages(channel, offset_date=since, reverse=True)
                    for msg in async_iter:
                        if not getattr(msg, "message", None):
                            continue
                        messages.append((msg.date, msg.message))
                        if len(messages) >= 30:
                            break

                    if not messages:
                        continue

                    messages.sort(key=lambda x: x[0], reverse=True)
                    latest_timestamp = messages[0][0]
                    combined_text = " ".join(text.replace("\n", " ").strip() for _, text in messages[:30])
                    themes = self._extract_themes(combined_text)

                    summary_lines = [
                        f"Channel: {channel}",
                        f"Messages: {len(messages)} (last {config.TELEGRAM_LOOKBACK_DAYS} days)",
                        "Key themes: " + (", ".join(themes) if themes else "No clear themes detected"),
                        "Highlights:",
                    ]
                    for ts, text in messages[:10]:
                        snippet = text.replace("\n", " ").strip()
                        if len(snippet) > 200:
                            snippet = snippet[:200] + "..."
                        summary_lines.append(f"- {ts.strftime('%Y-%m-%d %H:%M')}: {snippet}")

                    item = self._create_item(
                        title=f"Telegram: {channel}",
                        content="\n".join(summary_lines),
                        author="Telegram",
                        timestamp=latest_timestamp,
                        raw_path=f"telegram:{channel}",
                    )
                    items.append(item)
                    print(f"📨 Loaded Telegram: {channel} ({len(messages)} messages)")
                except Exception as e:
                    print(f"⚠️  Telegram channel failed {channel}: {e}")

        return items

    @staticmethod
    def _parse_channels(raw: str) -> List[str]:
        if not raw:
            return []
        channels = []
        for part in raw.split(","):
            value = part.strip()
            if not value:
                continue
            if "t.me/" in value:
                value = value.split("t.me/")[-1]
            value = value.split("?")[0]
            value = value.strip("/")
            if "/" in value:
                value = value.split("/")[0]
            if value.startswith("@"):
                value = value[1:]
            channels.append(value)
        return list(dict.fromkeys(channels))

    @staticmethod
    def _extract_themes(text: str, top_n: int = 5) -> List[str]:
        """Extract the most common content themes from channel messages."""
        stopwords = {
            "the", "and", "for", "with", "from", "this", "that", "have",
            "your", "they", "their", "about", "will", "what", "when",
            "there", "here", "which", "been", "also", "will", "just",
            "like", "them", "then", "some", "more", "also", "today",
            "message", "channel", "telegram", "post", "author",
        }
        words = re.findall(r"[A-Za-zÅÄÖåäö]+", text.lower())
        counts = {}
        for word in words:
            if len(word) < 4 or word in stopwords:
                continue
            counts[word] = counts.get(word, 0) + 1
        sorted_terms = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        return [term for term, _ in sorted_terms[:top_n]]

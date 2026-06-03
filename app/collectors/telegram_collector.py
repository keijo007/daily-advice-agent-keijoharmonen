"""
Telegram Collector - fetches recent messages from Telegram channels.

Requires Telethon user session (TELEGRAM_SESSION_STRING).
"""

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

                    summary_lines = [
                        f"Channel: {channel}",
                        f"Messages: {len(messages)} (last {config.TELEGRAM_LOOKBACK_DAYS} days)",
                        "Recent snippets:",
                    ]
                    for ts, text in messages[:10]:
                        snippet = text.replace("\n", " ").strip()
                        if len(snippet) > 160:
                            snippet = snippet[:160] + "..."
                        summary_lines.append(f"- {ts.strftime('%Y-%m-%d %H:%M')}: {snippet}")

                    item = self._create_item(
                        title=f"Telegram: {channel}",
                        content="\n".join(summary_lines),
                        author="Telegram",
                        timestamp=datetime.now(),
                        raw_path=f"telegram:{channel}",
                    )
                    items.append(item)
                    print(f"📨 Loaded Telegram: {channel}")
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

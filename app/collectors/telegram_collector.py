"""
Telegram Collector - fetches messages from Telegram channels (stub).

WHY THIS FILE EXISTS:
- Placeholder for Telegram integration
- Shows collector pattern for real-time APIs
- Demonstrates async/authentication approach

FUTURE IMPLEMENTATION:
- Connect to Telegram Bot API
- Read from channels you follow
- Read from group chats (with permission)
- Create ContentItem from messages

REQUIREMENTS (when implemented):
- python-telegram-bot

HOW IT WOULD WORK:
1. Set up Telegram bot with BOT_TOKEN
2. Get chat IDs from channels/groups
3. Fetch recent messages
4. Extract content, author, timestamp
5. Summarize long conversations

AUTHENTICATION:
- Get BOT_TOKEN from BotFather on Telegram
- Store in .env (never hardcode!)
- Request chat_id and message permissions

PRIVACY:
- Only read channels/groups you have access to
- Respect user privacy
- Don't share Telegram data without consent
"""

from typing import List
from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceType


class TelegramCollector(BaseCollector):
    """Telegram message collector (stub)."""
    
    def __init__(self):
        """Initialize Telegram collector."""
        super().__init__(SourceType.TELEGRAM)
    
    def collect(self) -> List[ContentItem]:
        """
        Collect messages from Telegram channels.
        
        FUTURE: Implement when you add python-telegram-bot
        
        Returns:
            Empty list for now
        """
        print("ℹ️  Telegram collector not yet implemented")
        print("   Future: Fetch messages from channels you follow")
        return []

"""
WhatsApp Export Collector - reads exported WhatsApp chat history.

WHY THIS FILE EXISTS:
- WhatsApp exports conversations as .txt files
- Reads exported chats for insights into your daily interactions
- Uses only exports (no scraping or API access)

HOW IT WORKS:
- Reads .txt files from data/whatsapp_exports/
- Parses WhatsApp export format: [HH:MM, DD/MM/YYYY] Author: Message
- Groups messages by conversation (filename = conversation)
- Each file becomes one ContentItem (one conversation per day)

AGENT RELEVANCE:
- Reader Agent: Sees what you discussed with contacts
- Reflection Agent: Can identify communication patterns
- Coach Agent: May suggest follow-ups or patterns

PRIVACY CONSIDERATIONS:
- Only reads local export files (no real-time access)
- You control what's exported
- Should NOT send raw message history to OpenAI
- Instead, summarize: "You discussed X with Y people"

EXTENSION IDEAS:
- Extract individual messages as separate items
- Parse sender to track communication frequency
- Group by contact/group name
- Sentiment analysis per conversation
- Timeline of interactions
"""

import re
from pathlib import Path
from datetime import datetime
from typing import List
from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceType
from app.config import config
from app.services.onedrive_client import OneDriveClient


class WhatsAppCollector(BaseCollector):
    """Collects WhatsApp conversation summaries from exported .txt files."""
    
    # WhatsApp export format: [HH:MM, DD/MM/YYYY] Author: Message
    WHATSAPP_PATTERN = r"\[(\d{1,2}):(\d{2}), (\d{1,2})/(\d{1,2})/(\d{4})\]"
    
    def __init__(self, export_dir: Path = None):
        """
        Initialize WhatsApp collector.
        
        Args:
            export_dir: Path to WhatsApp exports directory
        """
        super().__init__(SourceType.WHATSAPP)
        self.export_dir = export_dir or config.WHATSAPP_DIR
    
    def collect(self) -> List[ContentItem]:
        """
        Collect WhatsApp conversation summaries.
        
        Returns:
            List of ContentItem objects, one per conversation file
        """
        if config.ONEDRIVE_WHATSAPP_EXPORT_PATH:
            client = OneDriveClient()
            if client.enabled:
                return self._collect_from_onedrive(client)

        return self._collect_from_local()

    def _collect_from_onedrive(self, client: OneDriveClient) -> List[ContentItem]:
        items: List[ContentItem] = []
        files = client.list_files(config.ONEDRIVE_WHATSAPP_EXPORT_PATH)
        if not files:
            print("⚠️  No WhatsApp export files found in OneDrive")
            return items

        export_files = [f for f in files if f.lower().endswith(".txt")]
        print(f"💬 Found {len(export_files)} WhatsApp export files (OneDrive)")

        for filename in export_files:
            try:
                content = client.read_file(
                    f"{config.ONEDRIVE_WHATSAPP_EXPORT_PATH}/{filename}"
                )
                if not content:
                    continue

                summary = self._summarize_conversation(content)
                timestamp = self._extract_timestamp_from_content(content)
                title = f"WhatsApp: {Path(filename).stem}"

                if not self._is_recent(timestamp):
                    continue

                item = self._create_item(
                    title=title,
                    content=summary,
                    author="WhatsApp",
                    timestamp=timestamp,
                    raw_path=f"onedrive:{config.ONEDRIVE_WHATSAPP_EXPORT_PATH}/{filename}",
                )
                items.append(item)
                print(f"  ✓ Loaded: {title}")
            except Exception as e:
                print(f"  ✗ Error reading {filename}: {e}")

        return items

    def _collect_from_local(self) -> List[ContentItem]:
        items: List[ContentItem] = []

        if not self.export_dir.exists():
            print(f"⚠️  WhatsApp exports directory not found: {self.export_dir}")
            return items

        # Find all .txt files
        export_files = list(self.export_dir.glob("*.txt"))
        print(f"💬 Found {len(export_files)} WhatsApp export files")

        for file_path in export_files:
            try:
                content = file_path.read_text(encoding="utf-8")

                # Extract conversation metadata
                summary = self._summarize_conversation(content)

                # Use parsed timestamp or file modification time
                timestamp = self._extract_timestamp_from_content(content)
                title = f"WhatsApp: {file_path.stem}"

                if not self._is_recent(timestamp):
                    continue

                item = self._create_item(
                    title=title,
                    content=summary,
                    author="WhatsApp",
                    timestamp=timestamp,
                    raw_path=str(file_path),
                )
                items.append(item)
                print(f"  ✓ Loaded: {title}")

            except Exception as e:
                print(f"  ✗ Error reading {file_path.name}: {e}")

        return items

    def _extract_timestamp_from_content(self, content: str) -> datetime:
        for line in content.splitlines():
            match = re.match(self.WHATSAPP_PATTERN, line)
            if match:
                hour, minute, day, month, year = match.groups()
                try:
                    return datetime(
                        int(year), int(month), int(day), int(hour), int(minute)
                    )
                except Exception:
                    break
        return datetime.now()

    def _is_recent(self, timestamp: datetime) -> bool:
        delta = datetime.now() - timestamp
        return delta.days <= config.WHATSAPP_LOOKBACK_DAYS
    
    def _summarize_conversation(self, content: str) -> str:
        """
        Summarize a WhatsApp conversation instead of including raw messages.
        
        PRIVACY PROTECTION:
        - We don't send full chat to OpenAI
        - Just extract high-level info
        - This reduces data exposure
        """
        lines = content.strip().split("\n")
        
        # Count messages and participants
        participants = set()
        message_count = 0
        topics = []
        
        for line in lines:
            match = re.match(self.WHATSAPP_PATTERN, line)
            if match:
                message_count += 1
                # Extract author (name between ] and :)
                rest = line[match.end():] if match.end() < len(line) else ""
                if ":" in rest:
                    author = rest.split(":")[0].strip()
                    participants.add(author)
                    
                    # Extract message (basic topic detection)
                    message = rest.split(":", 1)[1].strip()
                    if len(message) > 50:
                        topics.append(message[:80])
        
        summary = f"Conversation with {len(participants)} participants: {', '.join(list(participants)[:3])}. "
        summary += f"Total messages: {message_count}. "
        if topics:
            summary += f"Key messages: {'. '.join(topics[:3])}"
        
        return summary

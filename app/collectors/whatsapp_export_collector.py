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
        items = []
        
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
                
                # Use file modification time
                timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                # Title is the conversation name (filename)
                title = f"WhatsApp: {file_path.stem}"
                
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

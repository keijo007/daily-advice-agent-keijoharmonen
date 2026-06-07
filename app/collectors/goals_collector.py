"""
Goals Collector - reads your personal goals file.

WHY THIS FILE EXISTS:
- Goals are reference points for reflection
- Reflection Agent uses goals to identify misalignments
- Coach Agent gives advice aligned with your goals

HOW IT WORKS:
- Reads a single goals file (OneDrive-synced path from .env)
- Treats the entire file as one ContentItem
- Can be plain text or markdown with structure

AGENT RELEVANCE:
- Reader Agent: Skips this
- Reflection Agent: Compares diary/actions against goals
- Coach Agent: Tailors advice to your stated goals

EXTENSION IDEAS:
- Parse YAML/JSON structure for goal categories
- Track goal progress over time
- Weight goals by importance
- Link goals to specific actions
"""

from pathlib import Path
from datetime import datetime
from typing import List
from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceType
from app.config import config
from app.services.onedrive_client import OneDriveClient


class GoalsCollector(BaseCollector):
    """Collects your personal goals from OneDrive or local fallback."""
    
    def __init__(self, goals_file: str = None):
        """
        Initialize goals collector.
        
        Args:
            goals_file: Path to local goals file (default: config.GOALS_FILE_PATH)
        """
        super().__init__(SourceType.GOALS)
        self.goals_file = Path(goals_file or config.GOALS_FILE_PATH)
        self.onedrive_path = config.ONEDRIVE_GOALS_FILE_PATH
    
    def collect(self) -> List[ContentItem]:
        """
        Collect goals from OneDrive, or fallback to local file if configured.
        
        Returns:
            List with single ContentItem, or empty if no file available
        """
        items = []
        
        if self.onedrive_path:
            client = OneDriveClient()
            if client.enabled:
                content = client.read_file(self.onedrive_path)
                if content:
                    timestamp = datetime.now()
                    item = self._create_item(
                        title="Your Goals",
                        content=content,
                        author="You",
                        timestamp=timestamp,
                        raw_path=self.onedrive_path,
                    )
                    items.append(item)
                    print(f"🎯 Loaded goals from OneDrive: {self.onedrive_path}")
                    return items
                else:
                    print(f"⚠️  Could not read goals from OneDrive: {self.onedrive_path}")
            else:
                print("⚠️  OneDrive client not configured for goals")

        if self.goals_file.exists():
            try:
                content = self.goals_file.read_text(encoding="utf-8")
                timestamp = datetime.fromtimestamp(self.goals_file.stat().st_mtime)
                item = self._create_item(
                    title="Your Goals",
                    content=content,
                    author="You",
                    timestamp=timestamp,
                    raw_path=str(self.goals_file),
                )
                items.append(item)
                print(f"🎯 Loaded goals from local file: {self.goals_file.name}")
            except Exception as e:
                print(f"✗ Error reading goals file: {e}")
        else:
            print("⚠️  Goals not found locally or on OneDrive")
            print("   Set ONEDRIVE_GOALS_FILE_PATH in .env to your OneDrive goals file")
        
        return items

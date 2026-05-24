"""
Diary Collector - reads local diary files.

WHY THIS FILE EXISTS:
- Reads your daily diary entries from data/diary/ folder
- Supports .md and .txt files
- Extracts dated entries for reflection

HOW IT WORKS:
- Scans data/diary/ for files
- Reads each file and treats it as one diary entry
- Timestamps based on file modification time or filename
- Each file = one ContentItem

AGENT RELEVANCE:
- Reflection Agent needs recent diary to analyze your thinking
- Reader Agent skips diary (it's not "new external input")
- Coach Agent uses diary context to give personalized advice

EXTENSION IDEAS:
- Add support for .docx files
- Extract timestamps from file names (e.g., 2024-01-15.md)
- Support subdirectories by date (e.g., 2024/01/15.md)
- Add markdown frontmatter parsing for tags/metadata
"""

from pathlib import Path
from datetime import datetime
from typing import List
from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceType
from app.config import config


class DiaryCollector(BaseCollector):
    """Collects diary entries from local .md and .txt files."""
    
    def __init__(self, diary_dir: Path = None):
        """
        Initialize diary collector.
        
        Args:
            diary_dir: Path to diary directory (default: config.DIARY_DIR)
        """
        super().__init__(SourceType.DIARY)
        self.diary_dir = diary_dir or config.DIARY_DIR
    
    def collect(self) -> List[ContentItem]:
        """
        Collect all diary entries from files.
        
        Returns:
            List of ContentItem objects, one per file
        """
        items = []
        
        # Ensure directory exists
        if not self.diary_dir.exists():
            print(f"⚠️  Diary directory not found: {self.diary_dir}")
            return items
        
        # Find all .md and .txt files
        diary_files = list(self.diary_dir.glob("*.md")) + list(self.diary_dir.glob("*.txt"))
        
        print(f"📖 Found {len(diary_files)} diary files")
        
        for file_path in diary_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Use file modification time as timestamp
                timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                # Title is the filename
                title = file_path.stem
                
                item = self._create_item(
                    title=title,
                    content=content,
                    author="You",
                    timestamp=timestamp,
                    raw_path=str(file_path),
                )
                items.append(item)
                
                print(f"  ✓ Loaded: {title}")
                
            except Exception as e:
                print(f"  ✗ Error reading {file_path.name}: {e}")
        
        return items

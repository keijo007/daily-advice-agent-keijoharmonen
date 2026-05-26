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
from app.services.onedrive_client import OneDriveClient


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
        if config.ONEDRIVE_DIARY_SHARE_URL or config.ONEDRIVE_DIARY2_SHARE_URL:
            client = OneDriveClient()
            if client.enabled:
                return self._collect_from_shared_links(client)

        if config.ONEDRIVE_DIARY_FILE_PATH:
            client = OneDriveClient()
            if client.enabled:
                return self._collect_from_onedrive_file(client)

        if config.ONEDRIVE_DIARY_PATH:
            client = OneDriveClient()
            if client.enabled:
                return self._collect_from_onedrive(client)

        return self._collect_from_local()

    def _collect_from_shared_links(self, client: OneDriveClient) -> List[ContentItem]:
        """Collect diary entries from OneDrive share links."""
        items: List[ContentItem] = []
        share_urls = [
            config.ONEDRIVE_DIARY_SHARE_URL,
            config.ONEDRIVE_DIARY2_SHARE_URL,
        ]

        for share_url in [url for url in share_urls if url]:
            content = client.read_shared_file(share_url)
            if not content:
                print(f"⚠️  OneDrive share not readable: {share_url}")
                continue

            title = "Shared Diary"
            timestamp = datetime.now()

            item = self._create_item(
                title=title,
                content=content,
                author="You",
                timestamp=timestamp,
                raw_path=f"onedrive_share:{share_url}",
            )
            items.append(item)
            print(f"  ✓ Loaded shared diary entry")

        return items

    def _collect_from_onedrive_file(self, client: OneDriveClient) -> List[ContentItem]:
        """Collect a single diary entry from OneDrive file path."""
        items: List[ContentItem] = []
        file_path = config.ONEDRIVE_DIARY_FILE_PATH

        items.extend(self._collect_from_onedrive_file_path(
            client,
            file_path,
            "Diary",
        ))

        if config.ONEDRIVE_WEEKLY_FILE_PATH:
            items.extend(self._collect_from_onedrive_file_path(
                client,
                config.ONEDRIVE_WEEKLY_FILE_PATH,
                "Weekly Reflection",
            ))

        return items

    def _collect_from_onedrive_file_path(
        self,
        client: OneDriveClient,
        file_path: str,
        fallback_title: str,
    ) -> List[ContentItem]:
        """Collect a single OneDrive file into a diary item."""
        items: List[ContentItem] = []

        content = client.read_file(file_path)
        if not content:
            print(f"⚠️  OneDrive diary file not found: {file_path}")
            return items

        title = Path(file_path).stem or fallback_title
        timestamp = self._parse_timestamp_from_filename(Path(file_path).name)

        item = self._create_item(
            title=title,
            content=content,
            author="You",
            timestamp=timestamp,
            raw_path=f"onedrive:{file_path}",
        )
        items.append(item)
        print(f"  ✓ Loaded: {title}")

        return items

    def _collect_from_onedrive(self, client: OneDriveClient) -> List[ContentItem]:
        """Collect diary entries from OneDrive folder."""
        items: List[ContentItem] = []
        folder_path = config.ONEDRIVE_DIARY_PATH

        files = client.list_files(folder_path)
        if not files:
            print(f"⚠️  No OneDrive diary files found: {folder_path}")
            return items

        diary_files = [name for name in files if name.endswith(".md") or name.endswith(".txt")]
        print(f"📖 Found {len(diary_files)} OneDrive diary files")

        for filename in diary_files:
            try:
                content = client.read_file(f"{folder_path}/{filename}")
                if not content:
                    print(f"  ✗ Empty or unreadable: {filename}")
                    continue

                timestamp = self._parse_timestamp_from_filename(filename)
                title = Path(filename).stem

                item = self._create_item(
                    title=title,
                    content=content,
                    author="You",
                    timestamp=timestamp,
                    raw_path=f"onedrive:{folder_path}/{filename}",
                )
                items.append(item)
                print(f"  ✓ Loaded: {title}")
            except Exception as e:
                print(f"  ✗ Error reading {filename}: {e}")

        return items

    def _collect_from_local(self) -> List[ContentItem]:
        """Collect diary entries from local files."""
        items: List[ContentItem] = []

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

    @staticmethod
    def _parse_timestamp_from_filename(filename: str) -> datetime:
        """Parse YYYY-MM-DD prefix, fallback to now."""
        try:
            return datetime.strptime(filename[:10], "%Y-%m-%d")
        except Exception:
            return datetime.now()

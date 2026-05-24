"""
YouTube Collector - fetches video transcripts (stub for future).

WHY THIS FILE EXISTS:
- Placeholder for future YouTube integration
- Shows how to structure a new collector
- Demonstrates extension point pattern

FUTURE IMPLEMENTATION:
- Fetch transcripts from videos you watched recently
- Extract captions/auto-generated subtitles
- Convert to ContentItem
- Reader Agent can summarize educational content

REQUIREMENTS (when implemented):
- youtube-transcript-api
- pytube (for metadata)

HOW IT WOULD WORK:
1. Read list of YouTube channel IDs or video URLs
2. Fetch recent videos from channels
3. Extract captions/transcripts
4. Create ContentItem from transcript

PRIVACY CONSIDERATION:
- YouTube watch history is private by default
- Can use: public subscription list, specific channels, or manual list
- Don't scrape without permission
"""

from pathlib import Path
from typing import List
from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceType


class YouTubeCollector(BaseCollector):
    """YouTube video transcript collector (stub)."""
    
    def __init__(self):
        """Initialize YouTube collector."""
        super().__init__(SourceType.YOUTUBE)
    
    def collect(self) -> List[ContentItem]:
        """
        Collect YouTube transcripts.
        
        FUTURE: Implement this when you add youtube-transcript-api
        
        Returns:
            Empty list for now
        """
        print("ℹ️  YouTube collector not yet implemented")
        print("   Future: Fetch transcripts from subscribed channels")
        return []

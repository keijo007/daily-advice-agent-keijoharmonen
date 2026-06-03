"""
Base Collector abstract class.

WHY THIS FILE EXISTS:
- Defines the interface that ALL collectors must implement
- Ensures consistent behavior: every collector returns ContentItem objects
- Makes it easy to add new data sources without breaking existing code

AGENT ARCHITECTURE CONCEPT:
- This is the INPUT LAYER for the agent
- Data enters the system through collectors
- The agent never knows about the original source format
- All sources are normalized to ContentItem

HOW TO EXTEND:
- Create a new file collector_*.py
- Implement the collect() method
- Return List[ContentItem]
- Add it to daily_pipeline.py
"""

from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from app.models import ContentItem, SourceType


class BaseCollector(ABC):
    """Abstract base class for all data collectors."""
    
    def __init__(self, source_type: SourceType):
        """
        Initialize collector.
        
        Args:
            source_type: Which SourceType enum this collector handles
        """
        self.source_type = source_type
        self.name = self.__class__.__name__
    
    @abstractmethod
    def collect(self) -> List[ContentItem]:
        """
        Collect data from this source.
        
        Must return list of ContentItem objects.
        Each item is normalized to the universal schema.
        
        PRIVATE DATA HANDLING:
        - Be careful what you extract
        - Don't collect more than necessary
        - Log what's being collected for privacy awareness
        
        Returns:
            List of ContentItem objects
        """
        pass
    
    def _create_item(
        self,
        title: str,
        content: str,
        author: str = "Unknown",
        timestamp: datetime = None,
        url: str = None,
        raw_path: str = None,
    ) -> ContentItem:
        """
        Helper method to create a ContentItem.
        
        This standardizes item creation across all collectors.
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        return ContentItem(
            source=self.source_type,
            title=title,
            content=content,
            author=author,
            timestamp=timestamp,
            url=url,
            raw_path=raw_path,
        )
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.source_type.value})"

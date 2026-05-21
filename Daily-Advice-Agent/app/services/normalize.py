"""
Normalize service - converts items to standard ContentItem format.

WHY THIS FILE EXISTS:
- Ensures all items have the same structure regardless of source
- Standardization is KEY to agent design
- Agents can trust the data format

HOW IT WORKS:
- Takes raw data (string, dict, object)
- Converts to ContentItem
- Validates required fields
- Fills in defaults

AGENT ARCHITECTURE:
- Part of the data processing pipeline
- AFTER: Collection (collectors/)
- BEFORE: Deduplication (deduplicate.py)
- Input: Raw items from collectors
- Output: List[ContentItem]

EXTENSION IDEAS:
- Add language detection/translation
- Clean up formatting (remove URLs, special chars)
- Extract named entities
- Sanitize private data
"""

from typing import Any, List
from app.models import ContentItem, SourceType
from datetime import datetime


def normalize_item(item: Any) -> ContentItem:
    """
    Normalize any item type to ContentItem.
    
    This is a pattern for making data interoperable.
    """
    
    # If already a ContentItem, return as-is
    if isinstance(item, ContentItem):
        return item
    
    # If it's a dict, extract fields
    if isinstance(item, dict):
        return ContentItem(
            source=SourceType(item.get("source", "diary")),
            title=str(item.get("title", "No Title"))[:200],
            content=str(item.get("content", "")),
            author=str(item.get("author", "Unknown"))[:100],
            timestamp=item.get("timestamp", datetime.now()),
            url=item.get("url"),
            raw_path=item.get("raw_path"),
        )
    
    # Otherwise, raise error (unsupported type)
    raise ValueError(f"Cannot normalize item of type {type(item)}")


def normalize_items(items: List[Any]) -> List[ContentItem]:
    """
    Normalize a list of items.
    
    Returns:
        List of ContentItem objects
    """
    normalized = []
    for item in items:
        try:
            normalized.append(normalize_item(item))
        except Exception as e:
            print(f"⚠️  Failed to normalize item: {e}")
    
    return normalized


def validate_item(item: ContentItem) -> bool:
    """
    Validate that an item has required fields.
    
    VALIDATION LOGIC:
    - source: Must be valid SourceType
    - title: Must not be empty (>= 1 char)
    - content: Must not be empty (>= 1 char)
    - author: Must not be empty
    - timestamp: Must be datetime object
    
    Returns:
        True if valid, False otherwise
    """
    
    if not isinstance(item.source, SourceType):
        return False
    
    if not item.title or len(item.title.strip()) == 0:
        return False
    
    if not item.content or len(item.content.strip()) == 0:
        return False
    
    if not item.author or len(item.author.strip()) == 0:
        return False
    
    if not isinstance(item.timestamp, datetime):
        return False
    
    return True

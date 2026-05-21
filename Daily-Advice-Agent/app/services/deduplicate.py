"""
Deduplication service - removes duplicate items.

WHY THIS FILE EXISTS:
- Same article might appear in multiple RSS feeds
- Same diary entry might be collected twice
- Duplicates waste tokens on OpenAI API (cost!)
- Need to track what's already been seen

HOW IT WORKS:
- Computes hash for each item
- Checks if hash exists in database
- Filters out items we've already analyzed

AGENT ARCHITECTURE:
- Part of the daily pipeline
- BEFORE storage: Prevent duplicates from being saved
- AFTER normalization: Works with standardized items
- Uses ContentItem.compute_hash()

HASH STRATEGY:
- Based on: source + content + author + timestamp
- Collision resistant but not cryptographically secure
- MD5 is sufficient for this use case

EXTENSION IDEAS:
- Similarity search (not just exact hash match)
- Track item URLs to detect re-shared content
- ML-based deduplication (sentence transformers)
"""

from typing import List, Set
from app.models import ContentItem


def compute_hash(item: ContentItem) -> str:
    """
    Compute unique hash for an item (delegates to item itself).
    
    This is already implemented in ContentItem.compute_hash()
    """
    return item.compute_hash()


def deduplicate_items(
    new_items: List[ContentItem],
    existing_hashes: Set[str],
) -> List[ContentItem]:
    """
    Filter out items that already exist (by hash).
    
    ALGORITHM:
    1. Compute hash for each new item
    2. Check if hash is in existing_hashes
    3. Return only new items (not seen before)
    
    Args:
        new_items: Items to check
        existing_hashes: Hashes of already-seen items (from database)
    
    Returns:
        Filtered list of new items
    """
    deduplicated = []
    
    for item in new_items:
        item_hash = compute_hash(item)
        
        # If hash not in existing set, it's new
        if item_hash not in existing_hashes:
            deduplicated.append(item)
            print(f"✓ New: {item.title[:50]}")
        else:
            print(f"- Duplicate: {item.title[:50]}")
    
    print(f"📊 {len(deduplicated)}/{len(new_items)} items are new")
    return deduplicated


def get_hashes_from_items(items: List[ContentItem]) -> Set[str]:
    """
    Convert list of items to set of hashes.
    
    Useful for converting database results to a set for fast lookup.
    """
    return {compute_hash(item) for item in items}

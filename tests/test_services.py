"""
Tests for services layer.

Tests normalize, deduplicate, and storage functions.

HOW TO RUN:
  pytest tests/test_services.py -v
"""

import pytest
from datetime import datetime
from tempfile import TemporaryDirectory
from pathlib import Path

from app.models import ContentItem, SourceType
from app.services.normalize import normalize_item, validate_item
from app.services.deduplicate import deduplicate_items, compute_hash
from app.services.storage import StorageService


class TestNormalization:
    """Test data normalization."""
    
    def test_normalize_dict_to_contentitem(self):
        """Test converting dict to ContentItem."""
        
        data = {
            "source": "diary",
            "title": "My Day",
            "content": "Today was good",
            "author": "You",
            "timestamp": datetime.now(),
        }
        
        item = normalize_item(data)
        
        assert isinstance(item, ContentItem)
        assert item.source == SourceType.DIARY
        assert item.title == "My Day"
        print("✓ Dictionary normalization works!")
    
    def test_normalize_contentitem_passthrough(self):
        """Test that ContentItem passes through unchanged."""
        
        original = ContentItem(
            source=SourceType.RSS,
            title="Article",
            content="Content",
            author="Author",
            timestamp=datetime.now(),
        )
        
        result = normalize_item(original)
        
        assert result is original  # Same object
        print("✓ ContentItem passthrough works!")
    
    def test_validate_good_item(self):
        """Test that valid item passes validation."""
        
        item = ContentItem(
            source=SourceType.DIARY,
            title="Valid Title",
            content="Valid content",
            author="Author",
            timestamp=datetime.now(),
        )
        
        assert validate_item(item) == True
        print("✓ Valid item passes validation!")
    
    def test_validate_empty_title(self):
        """Test that empty title fails validation."""
        
        item = ContentItem(
            source=SourceType.DIARY,
            title="",  # Empty!
            content="Content",
            author="Author",
            timestamp=datetime.now(),
        )
        
        assert validate_item(item) == False
        print("✓ Empty title correctly rejected!")


class TestDeduplication:
    """Test deduplication logic."""
    
    def test_duplicate_detection(self):
        """Test that duplicates are detected by hash."""
        
        # Create two identical items
        item1 = ContentItem(
            source=SourceType.DIARY,
            title="Same Title",
            content="Same content",
            author="You",
            timestamp=datetime(2024, 1, 15),
        )
        
        item2 = ContentItem(
            source=SourceType.DIARY,
            title="Same Title",
            content="Same content",
            author="You",
            timestamp=datetime(2024, 1, 15),
        )
        
        # Hashes should be identical
        hash1 = compute_hash(item1)
        hash2 = compute_hash(item2)
        
        assert hash1 == hash2
        print(f"✓ Duplicates produce same hash: {hash1}")
    
    def test_filter_duplicates(self):
        """Test that deduplicate_items filters correctly."""
        
        # Create items
        new_item = ContentItem(
            source=SourceType.RSS,
            title="New Article",
            content="New content",
            author="News",
            timestamp=datetime.now(),
        )
        
        duplicate_item = ContentItem(
            source=SourceType.RSS,
            title="Old Article",
            content="Old content",
            author="Old News",
            timestamp=datetime(2024, 1, 1),
        )
        
        # Existing hash (from old item)
        existing_hashes = {compute_hash(duplicate_item)}
        
        # Filter
        new_items = [new_item, duplicate_item]
        filtered = deduplicate_items(new_items, existing_hashes)
        
        # Only new item should remain
        assert len(filtered) == 1
        assert filtered[0].title == "New Article"
        print("✓ Deduplication filters correctly!")


class TestStorage:
    """Test SQLite storage."""
    
    def test_save_and_retrieve_item(self):
        """Test saving and retrieving items from database."""
        
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            storage = StorageService(db_path)
            
            # Create item
            item = ContentItem(
                source=SourceType.DIARY,
                title="Test Entry",
                content="Test content",
                author="You",
                timestamp=datetime(2024, 1, 15),
            )
            
            # Save
            saved = storage.save_content_item(item)
            assert saved == True
            
            # Verify hash exists
            hashes = storage.get_existing_hashes()
            item_hash = item.compute_hash()
            assert item_hash in hashes
            
            print("✓ Storage save/retrieve works!")

    def test_duplicate_prevention(self):
        """Test that saving duplicate is rejected."""
        
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            storage = StorageService(db_path)
            
            # Create item
            item = ContentItem(
                source=SourceType.DIARY,
                title="Entry",
                content="Content",
                author="You",
                timestamp=datetime(2024, 1, 15),
            )
            
            # Save first time
            result1 = storage.save_content_item(item)
            assert result1 == True
            
            # Try saving again (duplicate)
            result2 = storage.save_content_item(item)
            assert result2 == False  # Duplicate rejected
            
            print("✓ Duplicate prevention works!")


# Run tests with: pytest tests/test_services.py -v

"""Unit tests for Item model."""

import pytest
from datetime import datetime
from src.studyvault.models.item import Item


class TestItemRating:
    """Test rating functionality."""
    
    def test_rating_clamps_upper_bound(self):
        """Test rating clamped to max 5."""
        item = Item("Test", "Cat", "pdf")
        item.set_rating(10)
        
        assert item.rating == 5
    
    def test_rating_clamps_lower_bound(self):
        """Test rating clamped to min 1 (if non-zero)."""
        item = Item("Test", "Cat", "pdf")
        item.set_rating(-5)
        
        assert item.rating == 1
    
    def test_rating_allows_zero(self):
        """Test rating can be 0 (unrated)."""
        item = Item("Test", "Cat", "pdf")
        item.set_rating(0)
        
        assert item.rating == 0


class TestItemSerialization:
    """Test to_dict/from_dict for persistence."""
    
    def test_to_dict(self):
        """Test converting item to dictionary."""
        item = Item("Test Title", "Test Cat", "pdf")
        item.add_tag("tag1")
        item.set_rating(4)
        
        data = item.to_dict()
        
        assert data['title'] == "Test Title"
        assert data['category'] == "Test Cat"
        assert data['type'] == "pdf"
        assert data['rating'] == 4
        assert "tag1" in data['tags']
        assert 'id' in data
    
    def test_from_dict(self):
        """Test creating item from dictionary."""
        data = {
            'id': 'test-id-123',
            'title': 'Test',
            'category': 'Cat',
            'type': 'pdf',
            'tags': ['tag1', 'tag2'],
            'rating': 3,
        }
        
        item = Item.from_dict(data)
        
        assert item.id == 'test-id-123'
        assert item.title == 'Test'
        assert item.rating == 3
        assert len(item.tags) == 2
    
    def test_round_trip_serialization(self):
        """Test item -> dict -> item preserves data."""
        original = Item("Original", "Category", "video")
        original.add_tag("test")
        original.set_rating(5)
        
        data = original.to_dict()
        restored = Item.from_dict(data)
        
        assert restored.title == original.title
        assert restored.category == original.category
        assert restored.rating == original.rating
        assert restored.tags == original.tags


"""Unit tests for service layer."""

import pytest
from pathlib import Path
import tempfile
from datetime import datetime

from src.studyvault.services.import_service import ImportService
from src.studyvault.services.library_service import LibraryService
from src.studyvault.services.search_service import SearchService
from src.studyvault.models.item import Item
from src.studyvault.models.task import Task


class TestImportService:
    """Test import service."""
    
    def test_import_from_empty_directory(self):
        """Test importing from empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ImportService()
            items = service.import_from_directory(Path(tmpdir))
            
            assert len(items) == 0
    
    def test_import_supported_files(self):
        """Test importing supported file types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create test files
            (tmp_path / "note.txt").touch()
            (tmp_path / "doc.pdf").touch()
            (tmp_path / "lecture.mp3").touch()
            
            service = ImportService()
            items = service.import_from_directory(tmp_path)
            
            assert len(items) == 3
            assert any(item.type == "note" for item in items)
            assert any(item.type == "pdf" for item in items)
            assert any(item.type == "audio" for item in items)
    
    def test_import_sets_file_path(self):
        """Test that imported items have file_path set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "test.txt").touch()
            
            service = ImportService()
            items = service.import_from_directory(tmp_path)
            
            assert len(items) == 1
            assert items[0].file_path is not None
            assert "test.txt" in items[0].file_path


class TestLibraryService:
    """Test library service."""
    
    def test_add_and_get_items(self):
        """Test adding items to library."""
        service = LibraryService()
        item = Item("Test", "Cat", "pdf")
        
        service.add_item(item)
        
        assert len(service.get_items()) == 1
        assert service.get_items()[0].title == "Test"
    
    def test_delete_item(self):
        """Test deleting item."""
        service = LibraryService()
        item = Item("Test", "Cat", "pdf")
        service.add_item(item)
        
        result = service.delete_item(item)
        
        assert result is True
        assert len(service.get_items()) == 0
    
    def test_undo_delete(self):
        """Test undo after delete."""
        service = LibraryService()
        item = Item("Test", "Cat", "pdf")
        service.add_item(item)
        service.delete_item(item)
        
        # Undo the delete
        service.undo()
        
        assert len(service.get_items()) == 1
        assert service.get_items()[0].title == "Test"
    
    def test_add_and_get_task(self):
        """Test adding task to priority queue."""
        service = LibraryService()
        task = Task("item-1", 5, datetime.now(), "Test task")
        
        service.add_task(task)
        
        assert len(service.get_all_tasks()) == 1
    
    def test_get_next_task_priority_order(self):
        """Test that tasks are retrieved by priority."""
        service = LibraryService()
        
        # Add tasks with different priorities
        task_low = Task("item-1", 2, datetime.now(), "Low priority")
        task_high = Task("item-2", 8, datetime.now(), "High priority")
        task_med = Task("item-3", 5, datetime.now(), "Medium priority")
        
        service.add_task(task_low)
        service.add_task(task_high)
        service.add_task(task_med)
        
        # Should get highest priority first
        first = service.get_next_task()
        assert first.priority == 8
    
    def test_view_and_get_last_viewed(self):
        """Test recently viewed functionality."""
        service = LibraryService()
        item1 = Item("First", "Cat", "pdf")
        item2 = Item("Second", "Cat", "pdf")
        
        service.view_item(item1)
        service.view_item(item2)
        
        # Should get last viewed (LIFO)
        last = service.get_last_viewed()
        assert last.title == "Second"


class TestSearchService:
    """Test search service."""
    
    def test_build_index(self):
        """Test building search index."""
        service = SearchService()
        item = Item("Test Document", "Category", "pdf")
        item.add_tag("test-tag")
        
        service.build_index([item])
        
        keyword_index = service.get_keyword_index()
        assert "test" in keyword_index
        assert "document" in keyword_index
        assert "test-tag" in keyword_index
    
    def test_search_by_title_word(self):
        """Test searching by title word."""
        service = SearchService()
        item1 = Item("Python Tutorial", "Programming", "pdf")
        item2 = Item("Java Guide", "Programming", "pdf")
        
        service.build_index([item1, item2])
        
        item_map = {item1.id: item1, item2.id: item2}
        results = service.search("python", item_map)
        
        assert len(results) == 1
        assert results[0] == item1.id
    
    def test_search_by_tag(self):
        """Test searching by tag."""
        service = SearchService()
        item = Item("Document", "Category", "pdf")
        item.add_tag("algorithms")
        
        service.build_index([item])
        
        item_map = {item.id: item}
        results = service.search("algorithms", item_map)
        
        assert len(results) == 1
        assert results[0] == item.id
    
    def test_search_ranking_by_frequency(self):
        """Test that results are ranked by tag frequency."""
        service = SearchService()
        
        # Create items with same tag
        item1 = Item("Doc1", "Cat", "pdf")
        item1.add_tag("python")
        
        item2 = Item("Doc2", "Cat", "pdf")
        item2.add_tag("python")
        
        item3 = Item("Doc3", "Cat", "pdf")
        item3.add_tag("python")
        
        service.build_index([item1, item2, item3])
        
        # Tag frequency should affect ranking
        tag_freq = service.get_tag_frequency()
        assert tag_freq["python"] == 3
    
    def test_get_popular_tags(self):
        """Test getting popular tags."""
        service = SearchService()
        
        item1 = Item("Doc1", "Cat", "pdf")
        item1.add_tag("popular")
        
        item2 = Item("Doc2", "Cat", "pdf")
        item2.add_tag("popular")
        item2.add_tag("rare")
        
        service.build_index([item1, item2])
        
        popular = service.get_popular_tags(5)
        
        assert len(popular) == 2
        assert popular[0][0] == "popular"  # Most frequent first
        assert popular[0][1] == 2  # Frequency count

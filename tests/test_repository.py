"""Unit tests for repository layer."""

import pytest
from pathlib import Path
import tempfile
from datetime import datetime

from src.studyvault.repositories.library_repository import LibraryRepository, LibraryData
from src.studyvault.models.item import Item
from src.studyvault.models.task import Task


class TestLibraryData:
    """Test LibraryData dataclass."""
    
    def test_create_empty_library_data(self):
        """Test creating empty LibraryData."""
        data = LibraryData()
        
        assert len(data.items) == 0
        assert len(data.tasks) == 0
        assert len(data.keyword_index) == 0
        assert len(data.tag_frequency) == 0
    
    def test_create_library_data_with_items(self):
        """Test creating LibraryData with items."""
        item1 = Item("Item 1", "Cat 1", "pdf")
        item2 = Item("Item 2", "Cat 2", "video")
        
        data = LibraryData(items=[item1, item2])
        
        assert len(data.items) == 2
        assert data.items[0].title == "Item 1"


class TestLibraryRepositorySaveLoad:
    """Test save/load operations."""
    
    def test_save_and_load_empty_library(self):
        """Test saving and loading empty library."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LibraryRepository(Path(tmpdir) / "test.dat")
            
            # Save empty data
            data = LibraryData()
            repo.save_library(data)
            
            # Load it back
            loaded = repo.load_library()
            
            assert len(loaded.items) == 0
            assert len(loaded.tasks) == 0
    
    def test_save_and_load_items(self):
        """Test saving and loading items."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LibraryRepository(Path(tmpdir) / "test.dat")
            
            # Create items
            item1 = Item("Test Item", "Category", "pdf")
            item1.add_tag("test-tag")
            item1.set_rating(5)
            
            data = LibraryData(items=[item1])
            
            # Save
            repo.save_library(data)
            
            # Load
            loaded = repo.load_library()
            
            assert len(loaded.items) == 1
            assert loaded.items[0].title == "Test Item"
            assert loaded.items[0].rating == 5
            assert "test-tag" in loaded.items[0].tags
    
    def test_save_and_load_tasks(self):
        """Test saving and loading tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LibraryRepository(Path(tmpdir) / "test.dat")
            
            # Create tasks
            task1 = Task("item-1", 5, datetime.now(), "Task 1")
            task2 = Task("item-2", 8, datetime.now(), "Task 2")
            
            data = LibraryData(tasks=[task1, task2])
            
            # Save
            repo.save_library(data)
            
            # Load
            loaded = repo.load_library()
            
            assert len(loaded.tasks) == 2
    
    def test_save_and_load_indexes(self):
        """Test saving and loading keyword index and tag frequency."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LibraryRepository(Path(tmpdir) / "test.dat")
            
            # Create data with indexes
            keyword_index = {"keyword1": {"item-1", "item-2"}}
            tag_frequency = {"tag1": 5, "tag2": 3}
            
            data = LibraryData(
                keyword_index=keyword_index,
                tag_frequency=tag_frequency
            )
            
            # Save
            repo.save_library(data)
            
            # Load
            loaded = repo.load_library()
            
            assert "keyword1" in loaded.keyword_index
            assert loaded.tag_frequency["tag1"] == 5


class TestLibraryRepositoryValidation:
    """Test file validation."""
    
    def test_load_nonexistent_file_returns_empty(self):
        """Test loading nonexistent file returns empty LibraryData."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LibraryRepository(Path(tmpdir) / "nonexistent.dat")
            
            loaded = repo.load_library()
            
            assert len(loaded.items) == 0
    
    def test_load_invalid_magic_number(self):
        """Test loading file with invalid magic number."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "invalid.dat"
            
            # Write invalid file
            with open(file_path, 'wb') as f:
                f.write(b"BAD")  # Wrong magic number
                f.write(struct.pack('>I', 1))
            
            repo = LibraryRepository(file_path)
            
            with pytest.raises(IOError, match="Invalid file format"):
                repo.load_library()
    
    def test_load_unsupported_version(self):
        """Test loading file with future version number."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "future.dat"
            
            # Write file with future version
            with open(file_path, 'wb') as f:
                f.write(b"LIB")
                f.write(struct.pack('>I', 999))  # Future version
            
            repo = LibraryRepository(file_path)
            
            with pytest.raises(IOError, match="Unsupported file version"):
                repo.load_library()


class TestLibraryRepositoryUtilities:
    """Test utility methods."""
    
    def test_backup_library(self):
        """Test creating backup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LibraryRepository(Path(tmpdir) / "test.dat")
            
            # Save some data
            data = LibraryData(items=[Item("Test", "Cat", "pdf")])
            repo.save_library(data)
            
            # Create backup
            backup_path = repo.backup_library()
            
            assert backup_path.exists()
            assert "backup" in backup_path.name
    
    def test_delete_library(self):
        """Test deleting library file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LibraryRepository(Path(tmpdir) / "test.dat")
            
            # Save data
            repo.save_library(LibraryData())
            
            # Delete
            result = repo.delete_library()
            
            assert result is True
            assert not repo.data_file.exists()
    
    def test_get_file_size(self):
        """Test getting file size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LibraryRepository(Path(tmpdir) / "test.dat")
            
            # No file yet
            assert repo.get_file_size() == 0
            
            # Save data
            repo.save_library(LibraryData())
            
            # Should have size now
            assert repo.get_file_size() > 0


import struct  # Add this import at top

"""Unit tests for utility modules."""

import pytest
from pathlib import Path
import tempfile
import os

from src.studyvault.utils.file_util import FileUtil


class TestFileExtension:
    """Test file extension detection."""
    
    def test_get_extension_with_pdf(self):
        """Test extracting .pdf extension."""
        path = Path("document.pdf")
        assert FileUtil.get_file_extension(path) == ".pdf"
    
    def test_get_extension_case_insensitive(self):
        """Test extension is lowercase."""
        path = Path("notes.TXT")
        assert FileUtil.get_file_extension(path) == ".txt"
    
    def test_get_extension_no_extension(self):
        """Test file without extension."""
        path = Path("README")
        assert FileUtil.get_file_extension(path) == ""
    
    def test_get_extension_multiple_dots(self):
        """Test file with multiple dots."""
        path = Path("archive.tar.gz")
        assert FileUtil.get_file_extension(path) == ".gz"


class TestFileTypeDetection:
    """Test determine_type method."""
    
    def test_determine_type_text_file(self):
        """Test .txt maps to 'note'."""
        assert FileUtil.determine_type(Path("notes.txt")) == "note"
    
    def test_determine_type_markdown(self):
        """Test .md maps to 'note'."""
        assert FileUtil.determine_type(Path("README.md")) == "note"
    
    def test_determine_type_pdf(self):
        """Test .pdf maps to 'pdf'."""
        assert FileUtil.determine_type(Path("document.pdf")) == "pdf"
    
    def test_determine_type_audio(self):
        """Test .mp3 maps to 'audio'."""
        assert FileUtil.determine_type(Path("lecture.mp3")) == "audio"
    
    def test_determine_type_video(self):
        """Test .mp4 maps to 'video'."""
        assert FileUtil.determine_type(Path("tutorial.mp4")) == "video"
    
    def test_determine_type_unknown(self):
        """Test unsupported extension returns 'unknown'."""
        assert FileUtil.determine_type(Path("image.jpg")) == "unknown"


class TestSupportedFileCheck:
    """Test is_supported_file method."""
    
    def test_supported_extensions(self):
        """Test all supported extensions return True."""
        supported = [".txt", ".md", ".pdf", ".mp3", ".mp4"]
        for ext in supported:
            path = Path(f"file{ext}")
            assert FileUtil.is_supported_file(path) is True
    
    def test_unsupported_extension(self):
        """Test unsupported extension returns False."""
        path = Path("image.png")
        assert FileUtil.is_supported_file(path) is False


class TestDirectoryScanning:
    """Test recursive directory scanning."""
    
    def test_scan_empty_directory(self):
        """Test scanning empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            processed = set()
            files = FileUtil.scan_directory(Path(tmpdir), processed)
            
            assert len(files) == 0
    
    def test_scan_directory_with_files(self):
        """Test scanning directory with supported files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create test files
            (tmp_path / "note.txt").touch()
            (tmp_path / "doc.pdf").touch()
            (tmp_path / "audio.mp3").touch()
            (tmp_path / "image.jpg").touch()  # Unsupported
            
            processed = set()
            files = FileUtil.scan_directory(tmp_path, processed)
            
            # Should find 3 supported files (not .jpg)
            assert len(files) == 3
            assert len(processed) == 3
    
    def test_scan_nested_directories(self):
        """Test recursive scanning of subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create nested structure
            subdir = tmp_path / "subdir"
            subdir.mkdir()
            
            (tmp_path / "root.txt").touch()
            (subdir / "nested.pdf").touch()
            
            processed = set()
            files = FileUtil.scan_directory(tmp_path, processed)
            
            assert len(files) == 2
    
    def test_scan_prevents_duplicates(self):
        """Test that processed_paths prevents duplicate processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "file.txt").touch()
            
            processed = set()
            
            # First scan
            files1 = FileUtil.scan_directory(tmp_path, processed)
            # Second scan (should skip already processed)
            files2 = FileUtil.scan_directory(tmp_path, processed)
            
            assert len(files1) == 1
            assert len(files2) == 0  # Already processed
    
    def test_scan_nonexistent_directory(self):
        """Test scanning nonexistent directory returns empty list."""
        processed = set()
        files = FileUtil.scan_directory(Path("/nonexistent/path"), processed)
        
        assert len(files) == 0

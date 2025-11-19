"""
File Utility Module - Recursive directory scanning and file type detection.

Provides utilities for scanning directories recursively, detecting supported file types,
and preventing duplicate processing. Uses DFS traversal with deduplication via set.
"""

from pathlib import Path
from typing import List, Set
import logging
import stat as stat_module

from studyvault.utils.logger import get_logger

logger = get_logger(__name__)

class FileUtil:
    """
    Static utility class for file operations.
    
    Supports recursive directory scanning with deduplication for file types:
    - Text files: .txt, .md
    - Documents: .pdf, .docx, .pptx
    - Audio: .mp3
    - Video: .mp4
    """
    
    SUPPORTED_EXTENSIONS = {'.txt', '.md', '.pdf', '.mp3', '.mp4', '.docx', '.pptx'}
    
    # Class constant - created once instead of every function call
    TYPE_MAPPING = {
        '.txt': 'note',
        '.md': 'note',
        '.pdf': 'pdf',
        '.mp3': 'audio',
        '.mp4': 'video',
        '.docx': 'docx',
        '.pptx': 'ppt',  # Fixed: maps to 'ppt' not 'pptx'
    }
    
    @staticmethod
    def scan_directory(directory: Path, processed_paths: Set[str]) -> List[Path]:
        """
        Recursively scan directory for supported files (DFS traversal).
        
        Optimized: Check extension first, resolve only if needed
        
        Args:
            directory: Path object of directory to scan
            processed_paths: Set of already-processed absolute paths (mutated in-place)
        
        Returns:
            List of Path objects for found files
        
        Complexity: O(N) where N = total files in tree
        """
        found_files: List[Path] = []
        
        # Validation
        if directory is None or not directory.exists():
            if logger.isEnabledFor(logging.WARNING):
                logger.warning(f"Directory does not exist: {directory}")
            return found_files
        
        if not directory.is_dir():
            if logger.isEnabledFor(logging.WARNING):
                logger.warning(f"Path is not a directory: {directory}")
            return found_files
        
        try:
            # Iterate directory contents
            for item in directory.iterdir():
                try:
                    if item.is_dir():
                        # Recursive call for subdirectories (DFS)
                        found_files.extend(
                            FileUtil.scan_directory(item, processed_paths)
                        )
                    elif item.is_file():
                        # Optimized order: check extension FIRST (cheap filter)
                        ext = item.suffix.lower() if item.suffix else ""
                        
                        if ext not in FileUtil.SUPPORTED_EXTENSIONS:
                            continue  # Skip unsupported files early
                        
                        # Now resolve only for supported files
                        path_str = str(item.resolve())
                        
                        if path_str in processed_paths:
                            continue  # Skip duplicates
                        
                        # Add to results
                        found_files.append(item)
                        processed_paths.add(path_str)
                        
                        # Batch logging: only log every 100 files
                        if len(found_files) % 100 == 0:
                            if logger.isEnabledFor(logging.DEBUG):
                                logger.debug(f"Found {len(found_files)} files so far...")
                
                except PermissionError:
                    if logger.isEnabledFor(logging.WARNING):
                        logger.warning(f"Permission denied: {item}")
                    continue
        
        except PermissionError:
            if logger.isEnabledFor(logging.WARNING):  # ✅ Consistent severity
                logger.warning(f"Cannot access directory: {directory}")
        
        return found_files
    
    @staticmethod
    def get_file_extension(file_path: Path) -> str:
        """
        Get file extension in lowercase (includes dot).
        
        Consider using `path.suffix.lower()` directly instead of this function.
        
        Args:
            file_path: Path object of the file
        
        Returns:
            Extension string (e.g., ".pdf") or empty string if none
        """
        return file_path.suffix.lower() if file_path.suffix else ""
    
    @staticmethod
    def determine_type(file_path: Path) -> str:
        """
        Determine item type based on file extension.
        
        Optimized: Uses class constant instead of rebuilding dict
        
        Args:
            file_path: Path object of the file
        
        Returns:
            Type string ("note", "pdf", "audio", "video", "docx", "ppt", or "unknown")
        """
        ext = file_path.suffix.lower() if file_path.suffix else ""
        return FileUtil.TYPE_MAPPING.get(ext, 'unknown')
    
    @staticmethod
    def is_supported_file(file_path: Path) -> bool:
        """
        Check if file extension is supported.
        
        Args:
            file_path: Path object to check
        
        Returns:
            True if file extension is in SUPPORTED_EXTENSIONS
        """
        ext = file_path.suffix.lower() if file_path.suffix else ""
        return ext in FileUtil.SUPPORTED_EXTENSIONS
    
    @staticmethod
    def get_file_stats(file_path: Path) -> dict:
        """
        Get file metadata (size, modified time, etc.).
        
        Optimized: Single stat() call, no redundant is_file() check
        
        Args:
            file_path: Path object of the file
        
        Returns:
            Dictionary with file stats
        """
        try:
            stat_info = file_path.stat()
            return {
                'size_bytes': stat_info.st_size,
                'modified_time': stat_info.st_mtime,
                'is_readable': stat_module.S_ISREG(stat_info.st_mode),  # No extra syscall
            }
        except OSError as e:  # More specific exception
            if logger.isEnabledFor(logging.ERROR):
                logger.error(f"Cannot get stats for {file_path}: {e}")
            return {
                'size_bytes': 0,
                'modified_time': 0,
                'is_readable': False,
            }
    
    @staticmethod
    def get_supported_extensions_list() -> List[str]:
        """
        Get supported extensions as list (for ImportService.get_import_stats())
        
        Returns:
            List of supported extensions
        """
        return sorted(FileUtil.SUPPORTED_EXTENSIONS)

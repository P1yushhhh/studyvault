"""
Import Service - Handles recursive directory import and file processing.

Scans directories for supported files and creates Item objects with metadata.
Maintains processed paths to prevent duplicates across multiple imports.
"""

from pathlib import Path
from typing import List, Set

from studyvault.models.item import Item
from studyvault.utils.file_util import FileUtil
from studyvault.utils.logger import get_logger

logger = get_logger(__name__)


class ImportService:
    """
    Service for importing files from directories into the library.
    
    Recursively scans directories for supported file types (.txt, .md, .pdf, .mp3, .mp4)
    and creates Item objects with extracted metadata.
    
    Example:
        >>> service = ImportService()
        >>> items = service.import_from_directory(Path("./sample_data"))
        >>> print(f"Imported {len(items)} items")
    """
    
    def __init__(self):
        """Initialize import service with empty processed paths set."""
        self.processed_paths: Set[str] = set()
        logger.debug("ImportService initialized")
    
    def import_from_directory(self, directory: Path) -> List[Item]:
        """
        Import all supported files from a directory recursively.
        
        Scans directory tree using DFS, creates Item for each supported file.
        Automatically extracts filename as title, determines type from extension,
        and stores absolute file path.
        
        Args:
            directory: Path object of directory to scan
        
        Returns:
            List of imported Item objects
        
        Example:
            >>> service = ImportService()
            >>> items = service.import_from_directory(Path("./notes"))
            >>> for item in items:
            ...     print(f"{item.title} - {item.type}")
        """
        imported_items: List[Item] = []
        
        # Validate directory
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory}")
            return imported_items
        
        if not directory.is_dir():
            logger.error(f"Path is not a directory: {directory}")
            return imported_items
        
        logger.info(f"Starting import from: {directory}")
        
        # Scan for files
        files = FileUtil.scan_directory(directory, self.processed_paths)
        
        logger.debug(f"Found {len(files)} files to import")
        
        # Create Item for each file
        for file_path in files:
            try:
                # Determine type from extension
                file_type = FileUtil.determine_type(file_path)
                
                # Create Item with filename as title
                item = Item(
                    title=file_path.stem,  # Filename without extension
                    category="Imported",
                    type=file_type
                )
                
                # Store absolute file path
                item.file_path = str(file_path.resolve())
                
                imported_items.append(item)
                logger.debug(f"Imported: {item.title} ({file_type})")
            
            except Exception as e:
                logger.error(f"Failed to import {file_path}: {e}", exc_info=True)
                continue
        
        logger.info(f"Import complete: {len(imported_items)} items imported")
        
        return imported_items
    
    def get_processed_paths(self) -> Set[str]:
        """
        Get set of already-processed file paths.
        
        Useful for checking which files have been imported or for
        preventing re-import of the same files.
        
        Returns:
            Set of absolute file path strings
        """
        return self.processed_paths
    
    def clear_processed_paths(self) -> None:
        """
        Clear the processed paths cache.
        
        Call this if you want to allow re-importing previously imported files.
        """
        count = len(self.processed_paths)
        self.processed_paths.clear()
        logger.debug(f"Cleared {count} processed paths")
    
    def get_import_stats(self) -> dict:
        """
        Get statistics about import operations.
        
        Returns:
            Dictionary with import statistics
        """
        return {
            'total_processed': len(self.processed_paths),
            'supported_extensions': list(FileUtil.SUPPORTED_EXTENSIONS),
        }

"""
Import Service - Handles recursive directory import and file processing.

Scans directories for supported files and creates Item objects with metadata.
Maintains processed paths to prevent duplicates across multiple imports.
"""

from pathlib import Path
from typing import List, Set
import logging

from studyvault.models.item import Item
from studyvault.utils.file_util import FileUtil
from studyvault.utils.logger import get_logger

logger = get_logger(__name__)

class ImportService:
    """
    Service for importing files from directories into the library.
    
    Recursively scans directories for supported file types and creates Item objects.
    """
    
    # Class constant for batch logging
    LOG_BATCH_SIZE = 100
    
    def __init__(self):
        """Initialize import service with empty processed paths set."""
        self.processed_paths: Set[str] = set()
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("ImportService initialized")
    
    def import_from_directory(self, directory: Path) -> List[Item]:
        """
        Import all supported files from a directory recursively.
        
        Args:
            directory: Path object of directory to scan
        
        Returns:
            List of imported Item objects
        """
        imported_items: List[Item] = []
        
        # Validate directory
        if not directory.exists():
            if logger.isEnabledFor(logging.ERROR):
                logger.error(f"Directory does not exist: {directory}")
            return imported_items
        
        if not directory.is_dir():
            if logger.isEnabledFor(logging.ERROR):
                logger.error(f"Path is not a directory: {directory}")
            return imported_items
        
        if logger.isEnabledFor(logging.INFO):
            logger.info(f"Starting import from: {directory}")
        
        # Scan for files
        files = FileUtil.scan_directory(directory, self.processed_paths)
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Found {len(files)} files to import")
        
        # Batch counters for logging
        success_count = 0
        error_count = 0
        
        # Create Item for each file
        for file_path in files:
            try:
                # Determine type from extension
                file_type = FileUtil.determine_type(file_path)
                
                # Handle empty stem (hidden files like .gitignore)
                title = file_path.stem if file_path.stem else file_path.name
                if not title:  # Still empty (shouldn't happen but defensive)
                    title = "Untitled"
                
                # Derive category from parent directory or file type
                category = self._derive_category(file_path, file_type)
                
                # Create Item
                item = Item(
                    title=title,
                    category=category,
                    type=file_type
                )
                
                # Removed .resolve() - assume FileUtil returns resolved paths
                # If FileUtil doesn't resolve, add: file_path = file_path.resolve()
                item.file_path = str(file_path)
                
                imported_items.append(item)
                success_count += 1
                
                # Batch logging every N items
                if success_count % self.LOG_BATCH_SIZE == 0:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Imported {success_count} items so far...")
            
            except Exception as e:
                error_count += 1
                if logger.isEnabledFor(logging.ERROR):
                    logger.error(f"Failed to import {file_path}: {e}", exc_info=True)
                continue
        
        # Final summary log
        if logger.isEnabledFor(logging.INFO):
            logger.info(
                f"Import complete: {success_count} items imported, "
                f"{error_count} errors"
            )
        
        return imported_items
    
    def _derive_category(self, file_path: Path, file_type: str) -> str:
        """
        Derive category from file location or type.
        
        Args:
            file_path: Path to the file
            file_type: Determined file type
        
        Returns:
            Category string
        """
        # Try to use parent directory name
        parent_name = file_path.parent.name
        
        # Filter out common root directories
        ignore_dirs = {'Desktop', 'Downloads', 'Documents', 'Users', 'home'}
        if parent_name and parent_name not in ignore_dirs:
            return parent_name.capitalize()
        
        # Fallback to type-based category
        type_category_map = {
            'pdf': 'Documents',
            'docx': 'Documents',
            'ppt': 'Presentations',
            'video': 'Videos',
            'audio': 'Audio',
            'note': 'Notes',
        }
        
        return type_category_map.get(file_type, 'Imported')
    
    def get_processed_paths(self) -> Set[str]:
        """Get set of already-processed file paths."""
        return self.processed_paths
    
    def clear_processed_paths(self) -> None:
        """Clear the processed paths cache."""
        count = len(self.processed_paths)
        self.processed_paths.clear()
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Cleared {count} processed paths")
    
    def get_import_stats(self) -> dict:
        """Get statistics about import operations."""
        # Cache supported extensions list (minor optimization)
        return {
            'total_processed': len(self.processed_paths),
            'supported_extensions': FileUtil.get_supported_extensions_list(),
        }

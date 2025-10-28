"""
Library Repository - Handles data persistence using Pickle.

Implements binary serialization with custom header (magic number + version)
for validation. Saves/loads library data including items, tasks, and search indexes.
"""

import pickle
import struct
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import heapq

from studyvault.models.item import Item
from studyvault.models.task import Task
from studyvault.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LibraryData:
    """
    Data class for library state (replaces Java inner class).
    
    Contains all persisted data: items, tasks, and search indexes.
    
    Attributes:
        items: List of all library items
        tasks: Priority queue of tasks (stored as list for pickle)
        keyword_index: Map of keywords to item IDs
        tag_frequency: Map of tags to usage counts
    """
    items: List[Item] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)  # Stored as list, converted to heap
    keyword_index: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    tag_frequency: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Convert tasks list to heap for priority queue behavior."""
        if self.tasks:
            heapq.heapify(self.tasks)
            logger.debug(f"Heapified {len(self.tasks)} tasks")


class LibraryRepository:
    """
    Repository for saving/loading library data to disk.
    
    Uses Python's pickle with custom binary format:
    - Magic number: "LIB" (3 bytes)
    - Version: 1 (4 bytes, big-endian)
    - Pickled data: LibraryData object
    
    Example:
        >>> repo = LibraryRepository()
        >>> data = LibraryData(items=[item1, item2], tasks=[task1])
        >>> repo.save_library(data)
        >>> loaded = repo.load_library()
    """
    
    DATA_FILE = "data/library_data.dat"
    FILE_VERSION = 1
    MAGIC_NUMBER = b"LIB"  # 3 bytes
    
    def __init__(self, data_file: Optional[Path] = None):
        """
        Initialize repository with optional custom data file path.
        
        Args:
            data_file: Custom path for data file (default: data/library_data.dat)
        """
        if data_file:
            self.data_file = Path(data_file)
        else:
            self.data_file = Path(self.DATA_FILE)
        
        # Ensure data directory exists
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"LibraryRepository initialized with file: {self.data_file}")
    
    def save_library(self, data: LibraryData) -> None:
        """
        Save library data to disk with custom binary format.
        
        Format:
        1. Magic number "LIB" (3 bytes) - validates file type
        2. Version number (4 bytes, big-endian) - for compatibility
        3. Pickled LibraryData object - all data
        
        Args:
            data: LibraryData object to save
        
        Raises:
            IOError: If file cannot be written
            pickle.PickleError: If data cannot be serialized
        
        Example:
            >>> data = LibraryData(items=[item1, item2])
            >>> repo.save_library(data)
        """
        try:
            # Use temporary file for atomic write (safer)
            temp_file = self.data_file.with_suffix('.tmp')
            
            with open(temp_file, 'wb') as f:
                # Write magic number (3 bytes)
                f.write(self.MAGIC_NUMBER)
                
                # Write version (4 bytes, big-endian)
                f.write(struct.pack('>I', self.FILE_VERSION))
                
                # Pickle the data
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Atomic rename (replaces old file)
            temp_file.replace(self.data_file)
            
            logger.info(
                f"Library saved successfully: {len(data.items)} items, "
                f"{len(data.tasks)} tasks to {self.data_file}"
            )
        
        except Exception as e:
            logger.error(f"Failed to save library: {e}", exc_info=True)
            raise IOError(f"Cannot save library data: {e}") from e
    
    def load_library(self) -> LibraryData:
        """
        Load library data from disk with validation.
        
        Validates magic number and version before loading.
        Returns empty LibraryData if file doesn't exist.
        
        Returns:
            LibraryData object with loaded data (or empty if no file)
        
        Raises:
            IOError: If file format is invalid or version unsupported
            pickle.UnpickleError: If data is corrupted
        
        Example:
            >>> repo = LibraryRepository()
            >>> data = repo.load_library()
            >>> print(f"Loaded {len(data.items)} items")
        """
        # Return empty data if file doesn't exist
        if not self.data_file.exists():
            logger.info(f"No data file found at {self.data_file}, starting fresh")
            return LibraryData()
        
        try:
            with open(self.data_file, 'rb') as f:
                # Read and validate magic number (3 bytes)
                magic = f.read(3)
                if magic != self.MAGIC_NUMBER:
                    raise IOError(
                        f"Invalid file format. Expected {self.MAGIC_NUMBER}, "
                        f"got {magic}"
                    )
                
                # Read and validate version (4 bytes)
                version_bytes = f.read(4)
                if len(version_bytes) < 4:
                    raise IOError("Corrupted file: incomplete version header")
                
                version = struct.unpack('>I', version_bytes)[0]
                if version > self.FILE_VERSION:
                    raise IOError(
                        f"Unsupported file version {version}. "
                        f"Max supported: {self.FILE_VERSION}"
                    )
                
                # Unpickle the data
                data = pickle.load(f)
                
                # Validate it's a LibraryData instance
                if not isinstance(data, LibraryData):
                    raise IOError(f"Invalid data type: {type(data)}")
                
                logger.info(
                    f"Library loaded successfully: {len(data.items)} items, "
                    f"{len(data.tasks)} tasks from {self.data_file}"
                )
                
                return data
        
        except EOFError:
            logger.error("Corrupted file: unexpected end of file")
            return LibraryData()
        
        except Exception as e:
            logger.error(f"Failed to load library: {e}", exc_info=True)
            raise IOError(f"Cannot load library data: {e}") from e
    
    def backup_library(self, backup_path: Optional[Path] = None) -> Path:
        """
        Create a backup of the current library data file.
        
        Args:
            backup_path: Custom backup location (default: library_data_backup.dat)
        
        Returns:
            Path to the backup file
        
        Example:
            >>> repo.backup_library()
            PosixPath('data/library_data_backup.dat')
        """
        if not self.data_file.exists():
            raise FileNotFoundError(f"No data file to backup: {self.data_file}")
        
        if backup_path is None:
            backup_path = self.data_file.with_name(
                f"{self.data_file.stem}_backup{self.data_file.suffix}"
            )
        
        import shutil
        shutil.copy2(self.data_file, backup_path)
        
        logger.info(f"Backup created: {backup_path}")
        return backup_path
    
    def delete_library(self) -> bool:
        """
        Delete the library data file.
        
        Returns:
            True if file was deleted, False if it didn't exist
        
        Example:
            >>> repo.delete_library()
            True
        """
        if self.data_file.exists():
            self.data_file.unlink()
            logger.warning(f"Library data file deleted: {self.data_file}")
            return True
        return False
    
    def get_file_size(self) -> int:
        """
        Get the size of the data file in bytes.
        
        Returns:
            File size in bytes, or 0 if file doesn't exist
        """
        if self.data_file.exists():
            return self.data_file.stat().st_size
        return 0

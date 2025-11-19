"""
Library Repository - Handles data persistence using Pickle.

Implements binary serialization with custom header (magic number + version)
for validation. Saves/loads library data including items, tasks, and search indexes.
"""

import pickle
import struct
import shutil
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import heapq
import logging

from studyvault.models.item import Item
from studyvault.models.task import Task
from studyvault.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class LibraryData:
    """
    Data class for library state.
    
    Contains all persisted data: items, tasks, and search indexes.
    """
    items: List[Item] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    keyword_index: Dict[str, Set[str]] = field(default_factory=dict)  # ✅ Changed from defaultdict
    tag_frequency: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """
        Post-initialization: heapify tasks and restore defaultdict behavior.
        """
        # ✅ Restore defaultdict behavior after unpickling
        if not isinstance(self.keyword_index, defaultdict):
            self.keyword_index = defaultdict(set, self.keyword_index)
        
        # ✅ Heapify only if more than 1 task
        if len(self.tasks) > 1:
            heapq.heapify(self.tasks)
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Heapified {len(self.tasks)} tasks")

class LibraryRepository:
    """
    Repository for saving/loading library data to disk.
    
    Uses Python's pickle with custom binary format:
    - Magic number: "LIB" (3 bytes)
    - Version: 1 (4 bytes, big-endian)
    - Pickled data: LibraryData object
    """
    
    DATA_FILE = "data/library_data.dat"
    FILE_VERSION = 1
    MAGIC_NUMBER = b"LIB"
    
    def __init__(self, data_file: Optional[Path] = None):
        """Initialize repository with optional custom data file path."""
        if data_file:
            self.data_file = Path(data_file)
        else:
            self.data_file = Path(self.DATA_FILE)
        
        # ✅ Optimized: check before creating
        if not self.data_file.parent.exists():
            self.data_file.parent.mkdir(parents=True)
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"LibraryRepository initialized with file: {self.data_file}")
    
    def save_library(self, data: LibraryData) -> None:
        """
        Save library data to disk with custom binary format.
        
        ✅ Atomic write via temp file with cleanup on failure.
        """
        temp_file = self.data_file.with_suffix('.tmp')
        
        try:
            with open(temp_file, 'wb') as f:
                f.write(self.MAGIC_NUMBER)
                f.write(struct.pack('>I', self.FILE_VERSION))
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Atomic rename
            temp_file.replace(self.data_file)
            
            if logger.isEnabledFor(logging.INFO):
                logger.info(
                    f"Library saved: {len(data.items)} items, "
                    f"{len(data.tasks)} tasks to {self.data_file}"
                )
        
        except Exception as e:
            # ✅ Clean up temp file on failure
            if temp_file.exists():
                temp_file.unlink()
            
            if logger.isEnabledFor(logging.ERROR):
                logger.error(f"Failed to save library: {e}", exc_info=True)
            raise IOError(f"Cannot save library data: {e}") from e
    
    def load_library(self) -> LibraryData:
        """
        Load library data from disk with validation.
        
        ✅ Raises exception on corruption (instead of silent data loss).
        """
        if not self.data_file.exists():
            if logger.isEnabledFor(logging.INFO):
                logger.info(f"No data file found at {self.data_file}, starting fresh")
            return LibraryData()
        
        try:
            with open(self.data_file, 'rb') as f:
                # Validate magic number
                magic = f.read(3)
                if magic != self.MAGIC_NUMBER:
                    raise IOError(
                        f"Invalid file format. Expected {self.MAGIC_NUMBER}, got {magic}"
                    )
                
                # Validate version
                version_bytes = f.read(4)
                if len(version_bytes) < 4:
                    raise IOError("Corrupted file: incomplete version header")
                
                version = struct.unpack('>I', version_bytes)[0]
                if version > self.FILE_VERSION:
                    raise IOError(
                        f"Unsupported file version {version}. "
                        f"Max supported: {self.FILE_VERSION}"
                    )
                
                # Unpickle data
                data = pickle.load(f)
                
                if not isinstance(data, LibraryData):
                    raise IOError(f"Invalid data type: {type(data)}")
                
                if logger.isEnabledFor(logging.INFO):
                    logger.info(
                        f"Library loaded: {len(data.items)} items, "
                        f"{len(data.tasks)} tasks from {self.data_file}"
                    )
                
                return data
        
        except EOFError:
            # ✅ Raise exception instead of silent data loss
            if logger.isEnabledFor(logging.ERROR):
                logger.error("Corrupted file: unexpected end of file")
            raise IOError("Data file is corrupted (unexpected EOF)") from None
        
        except Exception as e:
            if logger.isEnabledFor(logging.ERROR):
                logger.error(f"Failed to load library: {e}", exc_info=True)
            raise IOError(f"Cannot load library data: {e}") from e
    
    def backup_library(self, backup_path: Optional[Path] = None) -> Path:
        """Create a backup of the current library data file."""
        if not self.data_file.exists():
            raise FileNotFoundError(f"No data file to backup: {self.data_file}")
        
        if backup_path is None:
            backup_path = self.data_file.with_name(
                f"{self.data_file.stem}_backup{self.data_file.suffix}"
            )
        
        shutil.copy2(self.data_file, backup_path)
        
        if logger.isEnabledFor(logging.INFO):
            logger.info(f"Backup created: {backup_path}")
        
        return backup_path
    
    def delete_library(self) -> bool:
        """Delete the library data file."""
        if self.data_file.exists():
            self.data_file.unlink()
            
            if logger.isEnabledFor(logging.WARNING):
                logger.warning(f"Library data file deleted: {self.data_file}")
            return True
        return False
    
    def get_file_size(self) -> int:
        """Get the size of the data file in bytes."""
        if self.data_file.exists():
            return self.data_file.stat().st_size
        return 0

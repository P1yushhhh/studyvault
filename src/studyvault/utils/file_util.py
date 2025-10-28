"""
File Utility Module - Recursive directory scanning and file type detection.

Provides utilities for scanning directories recursively, detecting supported file types,
and preventing duplicate processing. Uses DFS traversal with deduplication via set.
"""

from pathlib import Path
from typing import List, Set
from studyvault.utils.logger import get_logger


logger = get_logger(__name__)


class FileUtil:
    """
    Static utility class for file operations.
    
    Supports recursive directory scanning with deduplication for file types:
    - Text files: .txt, .md
    - Documents: .pdf
    - Audio: .mp3
    - Video: .mp4
    """
    
    SUPPORTED_EXTENSIONS = {'.txt', '.md', '.pdf', '.mp3', '.mp4'}
    
    @staticmethod
    def scan_directory(directory: Path, processed_paths: Set[str]) -> List[Path]:
        """
        Recursively scan directory for supported files (DFS traversal).
        
        Uses depth-first search to traverse subdirectories. Deduplicates files
        using the processed_paths set (O(1) lookups). Handles permission errors
        and invalid paths gracefully.
        
        Args:
            directory: Path object of directory to scan
            processed_paths: Set of already-processed absolute paths (for deduplication)
        
        Returns:
            List of Path objects for found files
        
        Example:
            >>> from pathlib import Path
            >>> processed = set()
            >>> files = FileUtil.scan_directory(Path("./sample_data"), processed)
            >>> len(files)
            42
        
        Complexity: O(N) where N = total files in tree
        """
        found_files: List[Path] = []
        
        # Validation
        if directory is None or not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return found_files
        
        if not directory.is_dir():
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
                        # Check if file is supported and not already processed
                        path_str = str(item.resolve())
                        ext = FileUtil.get_file_extension(item)
                        
                        if ext in FileUtil.SUPPORTED_EXTENSIONS and path_str not in processed_paths:
                            found_files.append(item)
                            processed_paths.add(path_str)
                            logger.debug(f"Found file: {item.name}")
                
                except PermissionError:
                    logger.warning(f"Permission denied: {item}")
                    continue
        
        except PermissionError:
            logger.error(f"Cannot access directory: {directory}")
        
        return found_files
    
    @staticmethod
    def get_file_extension(file_path: Path) -> str:
        """
        Get file extension in lowercase (includes dot).
        
        Args:
            file_path: Path object of the file
        
        Returns:
            Extension string (e.g., ".pdf") or empty string if none
        
        Example:
            >>> FileUtil.get_file_extension(Path("notes.PDF"))
            '.pdf'
            >>> FileUtil.get_file_extension(Path("README"))
            ''
        """
        if not file_path.suffix:
            return ""
        
        return file_path.suffix.lower()
    
    @staticmethod
    def determine_type(file_path: Path) -> str:
        """
        Determine item type based on file extension.
        
        Maps extensions to StudyVault item types:
        - .txt, .md → "note"
        - .pdf → "pdf"
        - .mp3 → "audio"
        - .mp4 → "video"
        
        Args:
            file_path: Path object of the file
        
        Returns:
            Type string ("note", "pdf", "audio", "video", or "unknown")
        
        Example:
            >>> FileUtil.determine_type(Path("lecture.mp4"))
            'video'
            >>> FileUtil.determine_type(Path("notes.txt"))
            'note'
        """
        ext = FileUtil.get_file_extension(file_path)
        
        # Map extension to type
        type_mapping = {
            '.txt': 'note',
            '.md': 'note',
            '.pdf': 'pdf',
            '.mp3': 'audio',
            '.mp4': 'video',
        }
        
        return type_mapping.get(ext, 'unknown')
    
    @staticmethod
    def is_supported_file(file_path: Path) -> bool:
        """
        Check if file extension is supported.
        
        Args:
            file_path: Path object to check
        
        Returns:
            True if file extension is in SUPPORTED_EXTENSIONS
        
        Example:
            >>> FileUtil.is_supported_file(Path("notes.pdf"))
            True
            >>> FileUtil.is_supported_file(Path("image.jpg"))
            False
        """
        ext = FileUtil.get_file_extension(file_path)
        return ext in FileUtil.SUPPORTED_EXTENSIONS
    
    @staticmethod
    def get_file_stats(file_path: Path) -> dict:
        """
        Get file metadata (size, modified time, etc.).
        
        Helper method for extracting file information during import.
        
        Args:
            file_path: Path object of the file
        
        Returns:
            Dictionary with file stats
        """
        try:
            stat = file_path.stat()
            return {
                'size_bytes': stat.st_size,
                'modified_time': stat.st_mtime,
                'is_readable': file_path.is_file(),
            }
        except Exception as e:
            logger.error(f"Cannot get stats for {file_path}: {e}")
            return {
                'size_bytes': 0,
                'modified_time': 0,
                'is_readable': False,
            }

"""
Logging Configuration - Centralized logging setup for StudyVault.

Provides a configured logger with file and console handlers.
Follows best practices: timestamped logs, rotating files, different levels for dev/prod.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(
    name: str = "studyvault",
    log_file: Optional[Path] = None,
    level: int = logging.DEBUG,
    console_level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configure and return a logger with file and console handlers.
    
    Creates a logger that writes to both file (detailed) and console (important messages only).
    Uses rotating file handler to prevent log files from growing indefinitely.
    
    Args:
        name: Logger name (usually "studyvault")
        log_file: Path to log file (default: data/logs/studyvault.log)
        level: Minimum log level for file (DEBUG = all messages)
        console_level: Minimum log level for console (INFO = skip debug messages)
        max_bytes: Max log file size before rotation (default 10MB)
        backup_count: Number of backup log files to keep
    
    Returns:
        Configured Logger instance
    
    Example:
        >>> from studyvault.utils.logger import setup_logger
        >>> logger = setup_logger()
        >>> logger.info("Application started")
        >>> logger.debug("Detailed debug info")
    """
    
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Default log file location
    if log_file is None:
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "studyvault.log"
    
    # Formatter with timestamp, level, module, and message
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler (rotating to prevent huge log files)
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file handler: {e}", file=sys.stderr)
    
    # Console handler (only important messages)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.debug(f"Logger '{name}' configured successfully")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger (for individual modules).
    
    Use this in individual modules instead of setup_logger.
    Inherits configuration from the root "studyvault" logger.
    
    Args:
        name: Module name (typically __name__)
    
    Returns:
        Logger instance for that module
    
    Example:
        # In models/item.py
        >>> from studyvault.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.debug("Item created")
    """
    return logging.getLogger(f"studyvault.{name}")


def set_log_level(level: int) -> None:
    """
    Change log level at runtime.
    
    Useful for debugging - can increase verbosity without restarting.
    
    Args:
        level: New log level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Example:
        >>> set_log_level(logging.DEBUG)  # Show all messages
        >>> set_log_level(logging.WARNING)  # Only warnings and errors
    """
    logger = logging.getLogger("studyvault")
    logger.setLevel(level)
    
    # Update all handlers
    for handler in logger.handlers:
        handler.setLevel(level)

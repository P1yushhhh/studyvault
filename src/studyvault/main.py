"""
StudyVault - Main Entry Point

Desktop application for organizing student study materials with intelligent search.
Port from JavaFX to PyQt6 with enhanced features and professional architecture.

Usage:
    python -m studyvault.main
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from studyvault.views.main_window import MainWindow
from studyvault.repositories.library_repository import LibraryRepository
from studyvault.utils.logger import setup_logger, get_logger

# Setup logging first (before any imports use logger)
setup_logger()
logger = get_logger(__name__)


class StudyVaultApp:
    """
    Main application class (equivalent to JavaFX App.java).
    
    Handles:
    - Application initialization
    - Window creation
    - Data loading/saving
    - Graceful shutdown
    
    Example:
        >>> app = StudyVaultApp()
        >>> app.run()
    """
    
    def __init__(self):
        """Initialize application."""
        # Create QApplication instance
        self.qapp = QApplication(sys.argv)
        self.qapp.setApplicationName("StudyVault")
        self.qapp.setOrganizationName("StudyVault")
        
        # Repository for persistence
        self.repository = LibraryRepository()
        
        # Main window (will be created in run())
        self.window: MainWindow = None
        
        logger.info("StudyVault application initialized")
    
    def run(self) -> int:
        """
        Run the application.
        
        Returns:
            Exit code (0 = success)
        """
        try:
            # Create main window
            self.window = MainWindow()
            
            # Load saved data
            self._load_data()
            
            # Apply stylesheet (optional)
            self._apply_stylesheet()
            
            # Setup auto-save on close
            self.qapp.aboutToQuit.connect(self._save_data)
            
            # Show window
            self.window.show()
            
            logger.info("Application started successfully!")
            
            # Run event loop
            return self.qapp.exec()
        
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            return 1
    
    def _load_data(self) -> None:
        """Load library data from disk."""
        try:
            data = self.repository.load_library()
            self.window.controller.load_data(data)
            
            logger.info(f"Loaded {len(data.items)} items from file")
            print(f"✓ Loaded {len(data.items)} items from previous session")
        
        except Exception as e:
            logger.info(f"No previous data found: {e}")
            print("Starting with empty library")
    
    def _save_data(self) -> None:
        """Save library data to disk (auto-save on close)."""
        try:
            data = self.window.controller.get_data()
            
            # Use the corrected save method signature
            self.repository.save_library(data)
            
            logger.info(f"Saved {len(data.items)} items successfully")
            print(f"✓ Data saved successfully ({len(data.items)} items)")
        
        except Exception as e:
            logger.error(f"Error saving data: {e}", exc_info=True)
            print(f"✗ Error saving data: {e}")
    
    def _apply_stylesheet(self) -> None:
        """Apply QSS stylesheet if exists."""
        # Get path relative to this file's location
        current_dir = Path(__file__).parent  # studyvault/ directory
        stylesheet_path = current_dir / "resources" / "css" / "styles.qss"
        if stylesheet_path.exists():
            try:
                with open(stylesheet_path, 'r') as f:
                    self.qapp.setStyleSheet(f.read())
                    logger.info("Stylesheet loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load stylesheet: {e}")
        
        else:
            logger.debug(f"No stylesheet found at: {stylesheet_path}")



def main():
    """
    Main entry point.
    
    Equivalent to Java's:
    public static void main(String[] args) {
        launch(args);
    }
    """
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create and run app
    app = StudyVaultApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()

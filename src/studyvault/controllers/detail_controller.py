"""
Detail Controller - Handles item detail view display.

Manages the detail panel that shows full information about a selected item.
Connects to DetailView widgets and updates display based on selected item.
"""

from typing import Optional
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import pyqtSlot

from studyvault.models.item import Item
from studyvault.utils.logger import get_logger

logger = get_logger(__name__)


class DetailController:
    """
    Controller for item detail view.
    
    Manages display of item details in a dedicated panel/dialog.
    Updates labels and widgets based on selected item.
    
    In PyQt6, controllers don't use @FXML decorators like JavaFX.
    Instead, we directly reference widgets passed from the view.
    
    Example:
        >>> controller = DetailController(title_label_widget)
        >>> controller.show_item(item)
    """
    
    def __init__(self, title_label: QLabel):
        """
        Initialize detail controller with UI widgets.
        
        Args:
            title_label: QLabel widget for displaying title
        
        Note: In full implementation, you'd pass all detail widgets
        (category_label, rating_label, tags_label, etc.)
        """
        self.title_label = title_label
        self.current_item: Optional[Item] = None
        
        logger.debug("DetailController initialized")
    
    def show_item(self, item: Item) -> None:
        """
        Display item details in the UI.
        
        Updates all detail widgets with item information.
        
        Args:
            item: Item to display
        
        Example:
            >>> controller.show_item(Item("DSP Notes", "Study", "pdf"))
        """
        if not item:
            logger.warning("Attempted to show None item")
            return
        
        self.current_item = item
        
        # Update title label
        self.title_label.setText(item.title)
        
        logger.info(f"Displaying item details: {item.title}")
    
    def clear_details(self) -> None:
        """Clear all detail displays."""
        self.title_label.setText("")
        self.current_item = None
        
        logger.debug("Cleared item details")
    
    def get_current_item(self) -> Optional[Item]:
        """
        Get the currently displayed item.
        
        Returns:
            Current Item, or None if nothing is displayed
        """
        return self.current_item

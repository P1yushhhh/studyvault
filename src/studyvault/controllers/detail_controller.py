"""
Detail Controller - Handles item detail view display.

Manages the detail panel that shows full information about a selected item.
Connects to DetailView widgets and updates display based on selected item.
"""

from typing import Optional, Protocol
import logging

from studyvault.models.item import Item
from studyvault.utils.logger import get_logger

logger = get_logger(__name__)

# ✅ NEW: Protocol for better testability
class TextDisplayWidget(Protocol):
    """Protocol for widgets that can display text."""
    def setText(self, text: str) -> None: ...

class DetailController:
    """
    Controller for item detail view.
    
    Manages display of item details in a dedicated panel/dialog.
    Updates labels and widgets based on selected item.
    """
    
    def __init__(self, title_widget: TextDisplayWidget):
        """
        Initialize detail controller with UI widgets.
        
        Args:
            title_widget: Widget for displaying title (must have setText method)
        
        Note: In full implementation, pass all detail widgets
        """
        self.title_widget = title_widget
        self.current_item: Optional[Item] = None
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("DetailController initialized")
    
    def show_item(self, item: Item) -> None:
        """
        Display item details in the UI.
        
        ✅ Fixed: Proper None check and empty title handling
        
        Args:
            item: Item to display
        """
        if item is None:  # ✅ Fixed: was 'if not item'
            if logger.isEnabledFor(logging.WARNING):
                logger.warning("Attempted to show None item")
            return
        
        self.current_item = item
        
        # ✅ Handle empty titles gracefully
        display_title = item.title if item.title else "(Untitled)"
        self.title_widget.setText(display_title)
        
        # ✅ Changed to DEBUG level (UI state change)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Displaying item: {item.title}")
    
    def clear_details(self) -> None:
        """Clear all detail displays."""
        self.title_widget.setText("")
        self.current_item = None
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Cleared item details")
    
    # ✅ Removed get_current_item() - use direct attribute access instead
    # Access via: controller.current_item
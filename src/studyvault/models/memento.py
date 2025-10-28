"""
Memento Model - Captures item state for undo operations.

Implements the Memento design pattern to save snapshots of Item objects
before destructive operations (delete, edit). Enables undo functionality
by restoring previous state from the saved snapshot.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
import logging
import copy

from src.studyvault.models.item import Item

logger = logging.getLogger(__name__)


@dataclass
class Memento:
    """
    Stores a snapshot of an Item for undo operations.
    
    Uses deep copy to preserve item state independently of the original.
    Timestamps allow tracking when the snapshot was created.
    
    Attributes:
        saved_item: Deep copy of the Item at time of snapshot
        operation_type: Type of operation ("DELETE" or "EDIT")
        timestamp: When the snapshot was created
    
    Example:
        >>> item = Item("Test", "Category", "pdf")
        >>> memento = Memento(item, "EDIT")
        >>> # Later, restore from memento
        >>> restored_item = memento.saved_item
    """
    
    saved_item: Item
    operation_type: Literal["DELETE", "EDIT"]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __init__(self, item: Item, operation_type: Literal["DELETE", "EDIT"]):
        """
        Create a memento with a deep copy of the item.
        
        Args:
            item: Item to create snapshot of
            operation_type: Type of operation ("DELETE" or "EDIT")
        """
        self.saved_item = self._deep_copy_item(item)
        self.operation_type = operation_type
        self.timestamp = datetime.now()
        
        logger.debug(f"Created Memento: {operation_type} for item {item.id}")
    
    def _deep_copy_item(self, original: Item) -> Item:
        """
        Create a deep copy of an Item (matches Java deepCopyItem).
        
        Uses copy.deepcopy for complete independence from original.
        Changes to the copy won't affect the original and vice versa.
        
        Args:
            original: Item to copy
        
        Returns:
            Deep copy of the item
        """
        # Python's copy.deepcopy handles all nested objects automatically
        # This is simpler than Java's manual field-by-field copying
        item_copy = copy.deepcopy(original)
        
        logger.debug(f"Deep copied item: {original.id}")
        return item_copy
    
    def get_saved_item(self) -> Item:
        """
        Get the saved item snapshot.
        
        Returns:
            The saved Item (deep copy at time of snapshot)
        """
        return self.saved_item
    
    def get_timestamp(self) -> datetime:
        """
        Get the snapshot timestamp.
        
        Returns:
            When the snapshot was created
        """
        return self.timestamp
    
    def get_operation_type(self) -> str:
        """
        Get the operation type.
        
        Returns:
            "DELETE" or "EDIT"
        """
        return self.operation_type
    
    def __str__(self) -> str:
        """String representation."""
        return f"Memento({self.operation_type}, {self.saved_item.title}, {self.timestamp.strftime('%Y-%m-%d %H:%M')})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"Memento(operation_type='{self.operation_type}', "
            f"item_id='{self.saved_item.id}', "
            f"timestamp='{self.timestamp.isoformat()}')"
        )
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation of the memento
        """
        return {
            'saved_item': self.saved_item.to_dict(),
            'operation_type': self.operation_type,
            'timestamp': self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Memento':
        """
        Create Memento from dictionary (for deserialization).
        
        Args:
            data: Dictionary with memento data
        
        Returns:
            New Memento instance
        """
        # Reconstruct the Item from dict
        saved_item = Item.from_dict(data['saved_item'])
        
        # Create memento (will create new timestamp by default)
        memento = cls.__new__(cls)  # Skip __init__ to manually set fields
        memento.saved_item = saved_item
        memento.operation_type = data['operation_type']
        
        # Parse timestamp from saved data
        timestamp_str = data.get('timestamp')
        if timestamp_str:
            memento.timestamp = datetime.fromisoformat(timestamp_str)
        else:
            memento.timestamp = datetime.now()
        
        return memento

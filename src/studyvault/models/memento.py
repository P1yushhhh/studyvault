"""
Memento Model - Captures item state for undo operations.
"""

from datetime import datetime
from typing import Literal
import copy
import logging

from studyvault.models.item import Item
from studyvault.utils.logger import get_logger

logger = get_logger(__name__)

class Memento:
    """
    Stores a snapshot of an Item for undo operations.
    
    Uses deep copy to preserve item state independently of the original.
    
    Attributes:
        saved_item: Deep copy of the Item at time of snapshot
        operation_type: Type of operation ("DELETE" or "EDIT")
        timestamp: When the snapshot was created
    """
    
    __slots__ = ('saved_item', 'operation_type', 'timestamp')  # Memory optimization
    
    def __init__(self, item: Item, operation_type: Literal["DELETE", "EDIT"], 
                 _precopied: bool = False):
        """
        Create a memento with a deep copy of the item.
        
        Args:
            item: Item to create snapshot of
            operation_type: Type of operation ("DELETE" or "EDIT")
            _precopied: Internal flag - if True, skip deepcopy (for from_dict)
        """
        # Single deepcopy call, no wrapper function
        self.saved_item = item if _precopied else copy.deepcopy(item)
        self.operation_type = operation_type
        self.timestamp = datetime.now()
        
        # Conditional logging
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Created Memento: {operation_type} for item {self.saved_item.id}")
    
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
        """Convert to dictionary for serialization."""
        return {
            'saved_item': self.saved_item.to_dict(),
            'operation_type': self.operation_type,
            'timestamp': self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Memento':
        """Create Memento from dictionary (for deserialization)."""
        saved_item = Item.from_dict(data['saved_item'])
        
        # Use _precopied flag to skip redundant deepcopy
        memento = cls(saved_item, data['operation_type'], _precopied=True)
        
        # Override timestamp with saved value
        timestamp_str = data.get('timestamp')
        if timestamp_str:
            memento.timestamp = datetime.fromisoformat(timestamp_str)
        
        return memento
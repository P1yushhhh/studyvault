"""
Task Model - Represents a task linked to a library item.

Tasks have priority (higher = more urgent), deadlines, and descriptions.
Implements comparison for priority queue sorting (max-heap behavior).
"""

from dataclasses import dataclass
from datetime import datetime
from functools import total_ordering
import logging
from studyvault.utils.logger import get_logger

logger = get_logger(__name__)

@total_ordering
@dataclass
class Task:
    """
    Represents a task associated with a library item.
    
    Tasks are sortable by priority (higher priority = more urgent).
    Used in a PriorityQueue for "next up" task management.
    
    Attributes:
        item_id: ID of the associated Item
        priority: Priority level (higher = more urgent, 1-10 recommended)
        deadline: When the task must be completed
        description: Task description/notes
    
    Example:
        >>> task = Task("item-123", priority=8, deadline=datetime.now(), description="Study DSP Chapter 3")
        >>> task2 = Task("item-456", priority=5, deadline=datetime.now(), description="Review OS notes")
        >>> task > task2  # True (8 > 5, higher priority comes first)
    """
    
    item_id: str
    priority: int
    deadline: datetime
    description: str
    
    def __post_init__(self):
        """Validate fields after initialization."""
        self._validate_item_id()
        self._validate_priority()
        self._validate_deadline()  
        self._validate_description()
        
        # Conditional logging
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Created Task: {self.item_id} - Priority {self.priority}")
    
    def _validate_string_field(self, value: str, field_name: str) -> str:
        """
        NEW: Shared validation for string fields (DRY).
        
        Args:
            value: String to validate
            field_name: Field name for error messages
        
        Returns:
            Stripped string
        """
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be string, got {type(value)}")
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"{field_name} cannot be empty")
        return stripped
    
    def _validate_item_id(self) -> None:
        """Validate item_id is non-empty string."""
        self.item_id = self._validate_string_field(self.item_id, "item_id")
    
    def _validate_priority(self) -> None:
        """Validate priority is positive integer."""
        if not isinstance(self.priority, int):
            raise TypeError(f"priority must be int, got {type(self.priority)}")
        if self.priority < 1:
            raise ValueError(f"priority must be >= 1, got {self.priority}")
    
    def _validate_deadline(self) -> None:
        """✅ NEW: Validate deadline is datetime."""
        if not isinstance(self.deadline, datetime):
            raise TypeError(f"deadline must be datetime, got {type(self.deadline)}")
    
    def _validate_description(self) -> None:
        """Validate description is non-empty string."""
        self.description = self._validate_string_field(self.description, "description")
    
    def __lt__(self, other: 'Task') -> bool:
        """
        Less-than comparison for sorting (implements Comparable).
        
        Higher priority comes FIRST (max-heap behavior).
        """
        if not isinstance(other, Task):
            return NotImplemented
        return self.priority > other.priority
    
    def __eq__(self, other: object) -> bool:
        """Equality comparison."""
        if not isinstance(other, Task):
            return NotImplemented
        return self.priority == other.priority
    
    def set_priority(self, value: int) -> None:
        """Update priority with validation."""
        if not isinstance(value, int):
            raise TypeError(f"priority must be int, got {type(value)}")
        if value < 1:
            raise ValueError(f"priority must be >= 1, got {value}")
        
        self.priority = value
        # Conditional logging, removed old_priority variable
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Task {self.item_id}: Priority updated to {value}")
    
    def set_deadline(self, value: datetime) -> None:
        """Update deadline with validation."""
        if not isinstance(value, datetime):
            raise TypeError(f"deadline must be datetime, got {type(value)}")
        
        self.deadline = value
        # Conditional logging, removed expensive isoformat()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Task {self.item_id}: Deadline updated")
    
    def set_description(self, value: str) -> None:
        """Update description with validation."""
        # Use shared validation helper
        self.description = self._validate_string_field(value, "description")
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Task {self.item_id}: Description updated")
    
    def __str__(self) -> str:
        """String representation."""
        return f"Task(priority={self.priority}, deadline={self.deadline.date()}, {self.description[:50]})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"Task(item_id='{self.item_id}', priority={self.priority}, "
            f"deadline={self.deadline.isoformat()}, description='{self.description[:30]}...')"
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'item_id': self.item_id,
            'priority': self.priority,
            'deadline': self.deadline.isoformat(),
            'description': self.description,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """Create Task from dictionary (for deserialization)."""
        deadline = data['deadline']
        if isinstance(deadline, str):
            deadline = datetime.fromisoformat(deadline)
        
        return cls(
            item_id=data['item_id'],
            priority=data['priority'],
            deadline=deadline,
            description=data['description'],
        )

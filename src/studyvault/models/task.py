"""
Task Model - Represents a task linked to a library item.

Tasks have priority (higher = more urgent), deadlines, and descriptions.
Implements comparison for priority queue sorting (max-heap behavior).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from functools import total_ordering
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
        self._validate_description()
        
        logger.debug(f"Created Task: {self.item_id} - Priority {self.priority}")
    
    def _validate_item_id(self) -> None:
        """Validate item_id is non-empty string."""
        if not isinstance(self.item_id, str):
            raise TypeError(f"item_id must be string, got {type(self.item_id)}")
        if not self.item_id.strip():
            raise ValueError("item_id cannot be empty")
        self.item_id = self.item_id.strip()
    
    def _validate_priority(self) -> None:
        """Validate priority is positive integer."""
        if not isinstance(self.priority, int):
            raise TypeError(f"priority must be int, got {type(self.priority)}")
        if self.priority < 1:
            raise ValueError(f"priority must be >= 1, got {self.priority}")
    
    def _validate_description(self) -> None:
        """Validate description is non-empty string."""
        if not isinstance(self.description, str):
            raise TypeError(f"description must be string, got {type(self.description)}")
        if not self.description.strip():
            raise ValueError("description cannot be empty")
        self.description = self.description.strip()
    
    def __lt__(self, other: 'Task') -> bool:
        """
        Less-than comparison for sorting (implements Comparable).
        
        Higher priority comes FIRST (max-heap behavior).
        In Java: return Integer.compare(other.priority, this.priority)
        In Python: self < other means self.priority > other.priority (reversed)
        
        Args:
            other: Another Task to compare
        
        Returns:
            True if self should come AFTER other in sorted order
        """
        if not isinstance(other, Task):
            return NotImplemented
        
        # Reverse comparison: higher priority = "less than" for max-heap
        return self.priority > other.priority
    
    def __eq__(self, other: object) -> bool:
        """
        Equality comparison.
        
        Args:
            other: Another Task to compare
        
        Returns:
            True if priorities are equal
        """
        if not isinstance(other, Task):
            return NotImplemented
        return self.priority == other.priority
    
    def set_priority(self, value: int) -> None:
        """
        Update priority with validation.
        
        Args:
            value: New priority value (must be >= 1)
        """
        if not isinstance(value, int):
            raise TypeError(f"priority must be int, got {type(value)}")
        if value < 1:
            raise ValueError(f"priority must be >= 1, got {value}")
        
        old_priority = self.priority
        self.priority = value
        logger.debug(f"Task {self.item_id}: Priority changed {old_priority} -> {value}")
    
    def set_deadline(self, value: datetime) -> None:
        """
        Update deadline with validation.
        
        Args:
            value: New deadline datetime
        """
        if not isinstance(value, datetime):
            raise TypeError(f"deadline must be datetime, got {type(value)}")
        
        self.deadline = value
        logger.debug(f"Task {self.item_id}: Deadline updated to {value.isoformat()}")
    
    def set_description(self, value: str) -> None:
        """
        Update description with validation.
        
        Args:
            value: New description string
        """
        if not isinstance(value, str):
            raise TypeError(f"description must be string, got {type(value)}")
        if not value.strip():
            raise ValueError("description cannot be empty")
        
        self.description = value.strip()
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
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation of the task
        """
        return {
            'item_id': self.item_id,
            'priority': self.priority,
            'deadline': self.deadline.isoformat(),
            'description': self.description,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """
        Create Task from dictionary (for deserialization).
        
        Args:
            data: Dictionary with task data
        
        Returns:
            New Task instance
        """
        deadline = data['deadline']
        if isinstance(deadline, str):
            deadline = datetime.fromisoformat(deadline)
        
        return cls(
            item_id=data['item_id'],
            priority=data['priority'],
            deadline=deadline,
            description=data['description'],
        )

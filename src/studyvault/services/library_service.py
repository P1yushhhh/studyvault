"""
Library Service - Core business logic for managing items and tasks.

Implements CRUD operations, undo functionality using Memento pattern,
recently viewed stack, and priority task queue management.
"""

from typing import List, Optional, Dict
import heapq
import logging
from collections import deque

from studyvault.models.item import Item
from studyvault.models.task import Task
from studyvault.models.memento import Memento
from studyvault.utils.logger import get_logger

logger = get_logger(__name__)

class LibraryService:
    """
    Main service for library operations.
    
    Manages items (CRUD), tasks (priority queue), recently viewed (stack),
    and undo operations (memento pattern).
    
    Data Structures Used:
    - List[Item]: O(1) append, for ordered storage
    - Dict[str, Item]: O(1) lookup by ID
    - List[Task] as heap: O(log n) push, O(log n) pop for priority queue
    - Deque for recent: O(1) append/pop from both ends (LIFO stack behavior)
    - Deque for undo: O(1) push/pop/auto-eviction 
    """
    
    MAX_RECENT_ITEMS = 50
    MAX_UNDO_STACK = 50
    
    def __init__(self):
        """Initialize library service with empty collections."""
        self.items: List[Item] = []
        self._id_index: Dict[str, Item] = {}  # O(1) ID lookup
        self.task_queue: List[Task] = []
        self.recently_viewed: deque = deque(maxlen=self.MAX_RECENT_ITEMS)
        self.undo_stack: deque = deque(maxlen=self.MAX_UNDO_STACK)  # Changed to deque
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("LibraryService initialized")
    
    # ===== Item Management =====
    
    def add_item(self, item: Item) -> None:
        """Add an item to the library."""
        self.items.append(item)
        self._id_index[item.id] = item  # Update index
        
        if logger.isEnabledFor(logging.INFO):
            logger.info(f"Added item: {item.title} (total: {len(self.items)})")
    
    def delete_item(self, item: Item) -> bool:
        """Delete an item with undo support."""
        # ✅ O(1) lookup instead of O(n)
        if item.id not in self._id_index:
            if logger.isEnabledFor(logging.WARNING):
                logger.warning(f"Cannot delete item: not found - {item.title}")
            return False
        
        # Save memento for undo
        memento = Memento(item, "DELETE")
        self.undo_stack.append(memento)  # Auto-eviction with deque maxlen
        
        # Remove item
        self.items.remove(item)  # Still O(n), but unavoidable for list
        del self._id_index[item.id]  # O(1) index cleanup
        
        if logger.isEnabledFor(logging.INFO):
            logger.info(f"Deleted item: {item.title} (undo available)")
        
        return True
    
    def update_item(self, old_item: Item, new_item: Item) -> bool:
        """Update an item with undo support."""
        # O(1) existence check
        if old_item.id not in self._id_index:
            if logger.isEnabledFor(logging.ERROR):
                logger.error(f"Cannot update item: not found - {old_item.title}")
            return False
        
        # Find index (still O(n) for list, but validated first)
        try:
            index = self.items.index(old_item)
        except ValueError:
            return False
        
        # Save memento for undo
        memento = Memento(old_item, "EDIT")
        self.undo_stack.append(memento)  # Auto-eviction
        
        # Update item
        self.items[index] = new_item
        self._id_index[new_item.id] = new_item  # Update index
        
        if logger.isEnabledFor(logging.INFO):
            logger.info(f"Updated item: {new_item.title}")
        
        return True
    
    def get_items(self) -> List[Item]:
        """Get all items in the library."""
        return self.items
    
    def find_item_by_id(self, item_id: str) -> Optional[Item]:
        """
        Find an item by ID.
        Now O(1) instead of O(n)
        """
        return self._id_index.get(item_id)
    
    # ===== Undo Operations =====
    
    def undo(self) -> bool:
        """Undo the last delete or edit operation."""
        if not self.undo_stack:
            if logger.isEnabledFor(logging.WARNING):
                logger.warning("Nothing to undo")
            return False
        
        memento = self.undo_stack.pop()
        operation_type = memento.operation_type  # Direct access (if Memento optimized)
        
        if operation_type == "DELETE":
            restored_item = memento.saved_item  # Direct access
            self.items.append(restored_item)
            self._id_index[restored_item.id] = restored_item  # Restore index
            
            if logger.isEnabledFor(logging.INFO):
                logger.info(f"Undo DELETE: restored {restored_item.title}")
            return True
        
        elif operation_type == "EDIT":
            saved_item = memento.saved_item  # Direct access
            
            # O(1) existence check first
            if saved_item.id not in self._id_index:
                if logger.isEnabledFor(logging.WARNING):
                    logger.warning(f"Cannot undo EDIT: item not found - {saved_item.id}")
                return False
            
            # Find and replace (still O(n) for list position)
            for i, item in enumerate(self.items):
                if item.id == saved_item.id:
                    self.items[i] = saved_item
                    self._id_index[saved_item.id] = saved_item  # Update index
                    
                    if logger.isEnabledFor(logging.INFO):
                        logger.info(f"Undo EDIT: restored {saved_item.title}")
                    return True
        
        return False
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0
    
    # ===== Task Management =====
    
    def add_task(self, task: Task) -> None:
        """Add a task to the priority queue."""
        heapq.heappush(self.task_queue, task)
        
        if logger.isEnabledFor(logging.INFO):
            logger.info(
                f"Added task: priority={task.priority}, "
                f"description={task.description[:30]}... (queue size: {len(self.task_queue)})"
            )
    
    def get_next_task(self) -> Optional[Task]:
        """Get and remove the highest priority task."""
        if not self.task_queue:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("No tasks in queue")
            return None
        
        task = heapq.heappop(self.task_queue)
        
        if logger.isEnabledFor(logging.INFO):
            logger.info(f"Retrieved task: priority={task.priority}, {task.description[:30]}...")
        
        return task
    
    def peek_next_task(self) -> Optional[Task]:
        """View the highest priority task without removing it."""
        if not self.task_queue:
            return None
        return self.task_queue[0]
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks (unsorted)."""
        return list(self.task_queue)
    
    # ===== Recently Viewed =====
    
    def view_item(self, item: Item) -> None:
        """Mark an item as viewed (adds to recently viewed stack)."""
        self.recently_viewed.append(item)
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Viewed item: {item.title} (recent count: {len(self.recently_viewed)})")
    
    def get_last_viewed(self) -> Optional[Item]:
        """Get and remove the last viewed item (LIFO)."""
        if not self.recently_viewed:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("No recently viewed items")
            return None
        
        item = self.recently_viewed.pop()
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Retrieved last viewed: {item.title}")
        
        return item
    
    def get_recent_history(self, count: int = 10) -> List[Item]:
        """Get recent viewing history without removing items."""
        # Optimized: single conversion + slice reverse
        return list(self.recently_viewed)[-count:][::-1]
    
    def clear_recent_history(self) -> None:
        """Clear the recently viewed history."""
        count = len(self.recently_viewed)
        self.recently_viewed.clear()
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Cleared {count} recently viewed items")
    
    # ===== Statistics =====
    
    def get_stats(self) -> dict:
        """Get library statistics."""
        return {
            'total_items': len(self.items),
            'total_tasks': len(self.task_queue),
            'recent_items': len(self.recently_viewed),
            'undo_available': len(self.undo_stack),
        }

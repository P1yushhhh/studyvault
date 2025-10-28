"""
Library Service - Core business logic for managing items and tasks.

Implements CRUD operations, undo functionality using Memento pattern,
recently viewed stack, and priority task queue management.
"""

from typing import List, Optional
import heapq
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
    - List[Item]: O(1) append, O(n) search/delete - acceptable for small datasets
    - List[Task] as heap: O(log n) push, O(log n) pop for priority queue
    - Deque for recent: O(1) append/pop from both ends (LIFO stack behavior)
    - List[Memento] as stack: O(1) push/pop for undo
    
    Example:
        >>> service = LibraryService()
        >>> item = Item("Test", "Category", "pdf")
        >>> service.add_item(item)
        >>> service.view_item(item)
        >>> last = service.get_last_viewed()
    """
    
    MAX_RECENT_ITEMS = 50  # Limit recently viewed to prevent memory issues
    MAX_UNDO_STACK = 50    # Limit undo history
    
    def __init__(self):
        """Initialize library service with empty collections."""
        self.items: List[Item] = []
        self.task_queue: List[Task] = []  # Min-heap for priority queue
        self.recently_viewed: deque = deque(maxlen=self.MAX_RECENT_ITEMS)
        self.undo_stack: List[Memento] = []
        
        logger.debug("LibraryService initialized")
    
    # ===== Item Management =====
    
    def add_item(self, item: Item) -> None:
        """
        Add an item to the library.
        
        Args:
            item: Item to add
        
        Example:
            >>> service.add_item(Item("Notes", "Study", "pdf"))
        """
        self.items.append(item)
        logger.info(f"Added item: {item.title} (total: {len(self.items)})")
    
    def delete_item(self, item: Item) -> bool:
        """
        Delete an item with undo support.
        
        Creates a memento before deletion to enable undo.
        
        Args:
            item: Item to delete
        
        Returns:
            True if item was deleted, False if not found
        
        Example:
            >>> service.delete_item(item)
            True
        """
        if item not in self.items:
            logger.warning(f"Cannot delete item: not found - {item.title}")
            return False
        
        # Save memento for undo
        memento = Memento(item, "DELETE")
        self.undo_stack.append(memento)
        
        # Limit undo stack size
        if len(self.undo_stack) > self.MAX_UNDO_STACK:
            self.undo_stack.pop(0)
            logger.debug("Undo stack limit reached, removed oldest memento")
        
        # Remove item
        self.items.remove(item)
        logger.info(f"Deleted item: {item.title} (undo available)")
        
        return True
    
    def update_item(self, old_item: Item, new_item: Item) -> bool:
        """
        Update an item with undo support.
        
        Creates a memento of the old state before updating.
        
        Args:
            old_item: Item to update
            new_item: New item data
        
        Returns:
            True if updated successfully
        """
        try:
            index = self.items.index(old_item)
            
            # Save memento for undo
            memento = Memento(old_item, "EDIT")
            self.undo_stack.append(memento)
            
            # Limit undo stack
            if len(self.undo_stack) > self.MAX_UNDO_STACK:
                self.undo_stack.pop(0)
            
            # Update item
            self.items[index] = new_item
            logger.info(f"Updated item: {new_item.title}")
            
            return True
        
        except ValueError:
            logger.error(f"Cannot update item: not found - {old_item.title}")
            return False
    
    def get_items(self) -> List[Item]:
        """
        Get all items in the library.
        
        Returns:
            List of all items
        """
        return self.items
    
    def find_item_by_id(self, item_id: str) -> Optional[Item]:
        """
        Find an item by ID.
        
        Args:
            item_id: Item ID to search for
        
        Returns:
            Item if found, None otherwise
        """
        for item in self.items:
            if item.id == item_id:
                return item
        return None
    
    # ===== Undo Operations =====
    
    def undo(self) -> bool:
        """
        Undo the last delete or edit operation.
        
        Restores item from memento. Currently only supports DELETE operations
        (adds item back to library).
        
        Returns:
            True if undo was performed, False if nothing to undo
        
        Example:
            >>> service.delete_item(item)
            >>> service.undo()  # Item is restored
            True
        """
        if not self.undo_stack:
            logger.warning("Nothing to undo")
            return False
        
        memento = self.undo_stack.pop()
        operation_type = memento.get_operation_type()
        
        if operation_type == "DELETE":
            # Restore deleted item
            restored_item = memento.get_saved_item()
            self.items.append(restored_item)
            logger.info(f"Undo DELETE: restored {restored_item.title}")
            return True
        
        elif operation_type == "EDIT":
            # Restore edited item (replace current with old version)
            saved_item = memento.get_saved_item()
            
            # Find and replace current version
            for i, item in enumerate(self.items):
                if item.id == saved_item.id:
                    self.items[i] = saved_item
                    logger.info(f"Undo EDIT: restored {saved_item.title}")
                    return True
            
            logger.warning(f"Cannot undo EDIT: item not found - {saved_item.id}")
            return False
        
        return False
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0
    
    # ===== Task Management =====
    
    def add_task(self, task: Task) -> None:
        """
        Add a task to the priority queue.
        
        Tasks are automatically sorted by priority (higher priority = processed first).
        Uses min-heap with reversed comparison (Task.__lt__ handles this).
        
        Args:
            task: Task to add
        
        Example:
            >>> task = Task("item-1", 8, datetime.now(), "Urgent task")
            >>> service.add_task(task)
        """
        heapq.heappush(self.task_queue, task)
        logger.info(
            f"Added task: priority={task.priority}, "
            f"description={task.description[:30]}... (queue size: {len(self.task_queue)})"
        )
    
    def get_next_task(self) -> Optional[Task]:
        """
        Get and remove the highest priority task.
        
        Returns:
            Highest priority Task, or None if queue is empty
        
        Example:
            >>> task = service.get_next_task()
            >>> if task:
            ...     print(f"Next: {task.description}")
        """
        if not self.task_queue:
            logger.debug("No tasks in queue")
            return None
        
        task = heapq.heappop(self.task_queue)
        logger.info(f"Retrieved task: priority={task.priority}, {task.description[:30]}...")
        
        return task
    
    def peek_next_task(self) -> Optional[Task]:
        """
        View the highest priority task without removing it.
        
        Returns:
            Highest priority Task, or None if queue is empty
        """
        if not self.task_queue:
            return None
        return self.task_queue[0]  # Min-heap root is at index 0
    
    def get_all_tasks(self) -> List[Task]:
        """
        Get all tasks (unsorted).
        
        Returns:
            List of all tasks in the queue
        """
        return list(self.task_queue)
    
    # ===== Recently Viewed =====
    
    def view_item(self, item: Item) -> None:
        """
        Mark an item as viewed (adds to recently viewed stack).
        
        Uses LIFO stack with max size limit to prevent memory issues.
        
        Args:
            item: Item that was viewed
        
        Example:
            >>> service.view_item(item)
        """
        self.recently_viewed.append(item)
        logger.debug(f"Viewed item: {item.title} (recent count: {len(self.recently_viewed)})")
    
    def get_last_viewed(self) -> Optional[Item]:
        """
        Get and remove the last viewed item (LIFO).
        
        Returns:
            Last viewed Item, or None if history is empty
        
        Example:
            >>> last = service.get_last_viewed()
            >>> if last:
            ...     print(f"Going back to: {last.title}")
        """
        if not self.recently_viewed:
            logger.debug("No recently viewed items")
            return None
        
        item = self.recently_viewed.pop()
        logger.debug(f"Retrieved last viewed: {item.title}")
        
        return item
    
    def get_recent_history(self, count: int = 10) -> List[Item]:
        """
        Get recent viewing history without removing items.
        
        Args:
            count: Number of recent items to return
        
        Returns:
            List of recently viewed items (most recent first)
        """
        # Return last 'count' items in reverse order (most recent first)
        return list(reversed(list(self.recently_viewed)[-count:]))
    
    def clear_recent_history(self) -> None:
        """Clear the recently viewed history."""
        count = len(self.recently_viewed)
        self.recently_viewed.clear()
        logger.debug(f"Cleared {count} recently viewed items")
    
    # ===== Statistics =====
    
    def get_stats(self) -> dict:
        """
        Get library statistics.
        
        Returns:
            Dictionary with various statistics
        """
        return {
            'total_items': len(self.items),
            'total_tasks': len(self.task_queue),
            'recent_items': len(self.recently_viewed),
            'undo_available': len(self.undo_stack),
        }

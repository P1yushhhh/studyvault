"""
Item Model - Core entity for library items.

Represents a study material item (note, PDF, audio, video) with metadata including
title, category, tags, rating, and file paths. Implements validation and serialization
for persistence.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import uuid4
import logging

# Setup logger
logger = logging.getLogger(__name__)


@dataclass
class Item:
    """
    Represents a library item with metadata.
    
    Attributes:
        title: Item title/name
        category: Category (e.g., "DSP Notes", "OS Lectures")
        type: Item type - "note", "pdf", "audio", or "video"
        id: Unique identifier (auto-generated UUID)
        tags: List of searchable tags
        rating: User rating (1-5, 0 = unrated)
        created_at: Creation timestamp
        media_url: Optional URL for online media
        file_path: Optional local file path
    
    Example:
        >>> item = Item(title="DSP Lecture 1", category="Digital Signal Processing", type="video")
        >>> item.add_tag("signals")
        >>> item.set_rating(5)
    """
    
    # Required fields (positional arguments)
    title: str
    category: str
    type: str
    
    # Auto-generated fields (use default_factory)
    id: str = field(default_factory=lambda: str(uuid4()))
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    # Optional fields with defaults
    rating: int = 0
    media_url: Optional[str] = None
    file_path: Optional[str] = None
    
    # Valid types constant
    VALID_TYPES = {"note", "pdf", "audio", "video"}
    
    def __post_init__(self):
        """
        Validate fields after initialization (SOLID: Single Responsibility).
        Called automatically by dataclass after __init__.
        """
        self._validate_title()
        self._validate_category()
        self._validate_type()
        self._validate_and_clamp_rating()
        
        logger.debug(f"Created Item: {self.id} - {self.title}")
    
    def _validate_title(self) -> None:
        """Validate title is non-empty string."""
        if not isinstance(self.title, str):
            raise TypeError(f"Title must be string, got {type(self.title)}")
        if not self.title.strip():
            raise ValueError("Title cannot be empty")
        self.title = self.title.strip()
    
    def _validate_category(self) -> None:
        """Validate category is non-empty string."""
        if not isinstance(self.category, str):
            raise TypeError(f"Category must be string, got {type(self.category)}")
        if not self.category.strip():
            raise ValueError("Category cannot be empty")
        self.category = self.category.strip()
    
    def _validate_type(self) -> None:
        """Validate type is one of allowed values."""
        if not isinstance(self.type, str):
            raise TypeError(f"Type must be string, got {type(self.type)}")
        
        type_lower = self.type.lower().strip()
        if type_lower not in self.VALID_TYPES:
            raise ValueError(
                f"Type must be one of {self.VALID_TYPES}, got '{self.type}'"
            )
        self.type = type_lower
    
    def _validate_and_clamp_rating(self) -> None:
        """Validate rating is 0-5 and clamp if needed (matches Java behavior)."""
        if not isinstance(self.rating, int):
            raise TypeError(f"Rating must be int, got {type(self.rating)}")
        
        # Clamp to 1-5 if non-zero (matches Java: Math.max(1, Math.min(5, rating)))
        if self.rating > 0:
            self.rating = max(1, min(5, self.rating))
        elif self.rating < 0:
            self.rating = 0
    
    def set_rating(self, value: int) -> None:
        """
        Set rating with automatic clamping to 1-5 range.
        
        Args:
            value: Rating value (will be clamped to 1-5 if non-zero)
        
        Example:
            >>> item.set_rating(10)  # Clamped to 5
            >>> item.rating
            5
        """
        if not isinstance(value, int):
            raise TypeError(f"Rating must be int, got {type(value)}")
        
        # Clamp to 1-5 if non-zero (matches Java logic)
        if value == 0:
            self.rating = 0
        else:
            self.rating = max(1, min(5, value))
        
        logger.debug(f"Item {self.id}: Rating set to {self.rating}")
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag if not already present (case-insensitive deduplication).
        
        Args:
            tag: Tag string to add
        
        Example:
            >>> item.add_tag("algorithms")
            >>> item.add_tag("Algorithms")  # Ignored (duplicate)
            >>> item.tags
            ['algorithms']
        """
        if not isinstance(tag, str):
            raise TypeError(f"Tag must be string, got {type(tag)}")
        
        tag_clean = tag.strip().lower()
        if not tag_clean:
            logger.warning("Attempted to add empty tag")
            return
        
        # Case-insensitive duplicate check
        if tag_clean not in [t.lower() for t in self.tags]:
            self.tags.append(tag_clean)
            logger.debug(f"Item {self.id}: Added tag '{tag_clean}'")
        else:
            logger.debug(f"Item {self.id}: Tag '{tag_clean}' already exists")
    
    def remove_tag(self, tag: str) -> bool:
        """
        Remove a tag (case-insensitive).
        
        Args:
            tag: Tag to remove
        
        Returns:
            True if tag was removed, False if not found
        """
        tag_clean = tag.strip().lower()
        for existing_tag in self.tags:
            if existing_tag.lower() == tag_clean:
                self.tags.remove(existing_tag)
                logger.debug(f"Item {self.id}: Removed tag '{existing_tag}'")
                return True
        return False
    
    def __str__(self) -> str:
        """String representation (matches Java toString)."""
        return f"{self.title} ({self.category})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"Item(id='{self.id[:8]}...', title='{self.title}', "
            f"category='{self.category}', type='{self.type}', "
            f"rating={self.rating}, tags={len(self.tags)})"
        )
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization/export.
        
        Returns:
            Dictionary representation of the item
        """
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'type': self.type,
            'tags': self.tags.copy(),  # Return copy to prevent external modification
            'rating': self.rating,
            'created_at': self.created_at.isoformat(),
            'media_url': self.media_url,
            'file_path': self.file_path,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Item':
        """
        Create Item from dictionary (for deserialization).
        
        Args:
            data: Dictionary with item data
        
        Returns:
            New Item instance
        """
        item = cls(
            title=data['title'],
            category=data['category'],
            type=data['type'],
        )
        item.id = data.get('id', item.id)
        item.tags = data.get('tags', []).copy()
        item.rating = data.get('rating', 0)
        item.media_url = data.get('media_url')
        item.file_path = data.get('file_path')
        
        # Parse datetime if present
        if 'created_at' in data:
            if isinstance(data['created_at'], str):
                item.created_at = datetime.fromisoformat(data['created_at'])
            else:
                item.created_at = data['created_at']
        
        return item
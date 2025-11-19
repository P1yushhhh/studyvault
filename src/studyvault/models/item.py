"""
Item Model - Core entity for library items.

Now supports:
- URL-only items (no local file)
- Extra file types (docx, ppt)
- Clean separation between local files and web URLs
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import logging
from uuid import uuid4
from studyvault.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class Item:
    title: str
    category: str
    type: str

    id: str = field(default_factory=lambda: uuid4().hex)  
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    rating: int = 0
    file_path: Optional[str] = None
    url: Optional[str] = None

    VALID_TYPES = {"note", "pdf", "docx", "ppt", "audio", "video", "url"}

    def __post_init__(self):
        # Single strip call per field
        self.title = self._validate_and_strip_field(self.title, "Title")
        self.category = self._validate_and_strip_field(self.category, "Category")
        self._validate_type()
        self._validate_and_clamp_rating()
        
        # Conditional logging
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Created Item: {self.id} - {self.title}")

    # ---------- Validation ----------

    def _validate_and_strip_field(self, value: str, field_name: str) -> str:
        """Validate and strip a string field. Single strip call."""
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"{field_name} cannot be empty.")
        return stripped

    def _validate_type(self) -> None:
        if not isinstance(self.type, str):
            raise TypeError("Type must be a string.")
        self.type = self.type.strip().lower()  # Strip before lower
        if self.type not in self.VALID_TYPES:
            raise ValueError(f"Type must be one of {self.VALID_TYPES}, got '{self.type}'")

    def _validate_and_clamp_rating(self) -> None:
        if not isinstance(self.rating, int):
            raise TypeError(f"Rating must be int, got {type(self.rating)}")
        self.rating = max(0, min(5, self.rating))  # Single expression

    # ---------- Public Methods ----------

    def set_rating(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("Rating must be int.")
        self.rating = max(0, min(5, value))
        # Conditional logging
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Item {self.id}: Rating set to {self.rating}")

    def add_tag(self, tag: str) -> None:
        if not isinstance(tag, str):
            raise TypeError("Tag must be string.")
        tag_clean = tag.strip().lower()
        # Fixed: tags already stored lowercase, no list comp needed
        if tag_clean and tag_clean not in self.tags:
            self.tags.append(tag_clean)

    # ---------- Serialization ----------

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'type': self.type,
            'tags': self.tags.copy(),
            'rating': self.rating,
            'created_at': self.created_at.isoformat(),
            'file_path': self.file_path,
            'url': self.url,         
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Item':
        item = cls(
            title=data['title'],
            category=data['category'],
            type=data['type'],
        )
        item.id = data.get('id', item.id)
        item.tags = data.get('tags', []).copy()
        # Validate rating on deserialization
        item.set_rating(data.get('rating', 0))
        item.file_path = data.get('file_path')
        item.url = data.get('url')

        if 'created_at' in data:
            if isinstance(data['created_at'], str):
                item.created_at = datetime.fromisoformat(data['created_at'])
            else:
                item.created_at = data['created_at']

        return item

    def __str__(self) -> str:
        return f"{self.title} ({self.category})"
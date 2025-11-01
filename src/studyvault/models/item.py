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
from uuid import uuid4
from studyvault.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class Item:
    title: str
    category: str
    type: str

    id: str = field(default_factory=lambda: str(uuid4()))
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    rating: int = 0
    file_path: Optional[str] = None      # Local file path (pdf/docx/ppt/audio/video)
    url: Optional[str] = None            # Remote resource (YouTube, website, etc.)

    # ✅ Extended valid item types
    VALID_TYPES = {"note", "pdf", "docx", "ppt", "audio", "video", "url"}

    def __post_init__(self):
        self._validate_title()
        self._validate_category()
        self._validate_type()
        self._validate_and_clamp_rating()
        logger.debug(f"Created Item: {self.id} - {self.title}")

    # ---------- Validation ----------

    def _validate_title(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("Title cannot be empty.")
        self.title = self.title.strip()

    def _validate_category(self) -> None:
        if not isinstance(self.category, str) or not self.category.strip():
            raise ValueError("Category cannot be empty.")
        self.category = self.category.strip()

    def _validate_type(self) -> None:
        if not isinstance(self.type, str):
            raise TypeError("Type must be a string.")
        type_lower = self.type.lower().strip()
        if type_lower not in self.VALID_TYPES:
            raise ValueError(f"Type must be one of {self.VALID_TYPES}, got '{self.type}'")
        self.type = type_lower

    def _validate_and_clamp_rating(self) -> None:
        if not isinstance(self.rating, int):
            raise TypeError(f"Rating must be int, got {type(self.rating)}")
        if self.rating < 0:
            self.rating = 0
        if self.rating > 5:
            self.rating = 5

    # ---------- Public Methods ----------

    def set_rating(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("Rating must be int.")
        self.rating = max(0, min(5, value))
        logger.debug(f"Item {self.id}: Rating set to {self.rating}")

    def add_tag(self, tag: str) -> None:
        if not isinstance(tag, str):
            raise TypeError("Tag must be string.")
        tag_clean = tag.strip().lower()
        if tag_clean and tag_clean not in [t.lower() for t in self.tags]:
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
            'url': self.url,          # ✅ New field
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
        item.rating = data.get('rating', 0)
        item.file_path = data.get('file_path')
        item.url = data.get('url')  # ✅ Restore URL

        if 'created_at' in data:
            if isinstance(data['created_at'], str):
                item.created_at = datetime.fromisoformat(data['created_at'])
            else:
                item.created_at = data['created_at']

        return item

    def __str__(self) -> str:
        return f"{self.title} ({self.category})"
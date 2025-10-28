"""
Search Service - Keyword indexing and ranked search functionality.

Builds inverted index (keyword -> item IDs) for O(1) lookups.
Ranks results by tag frequency using priority queue.
"""

from typing import List, Dict, Set, Optional
from collections import defaultdict
import heapq
from dataclasses import dataclass

from studyvault.models.item import Item
from studyvault.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ItemRank:
    """
    Helper class for ranking search results (replaces Java inner class).
    
    Implements comparison for use in PriorityQueue (max-heap behavior).
    """
    item_id: str
    frequency: int
    
    def __lt__(self, other: 'ItemRank') -> bool:
        """Higher frequency comes first (max-heap)."""
        return self.frequency > other.frequency


class SearchService:
    """
    Service for building search indexes and performing ranked searches.
    
    Data Structures:
    - HashMap (dict): keyword -> set of item IDs for O(1) exact match
    - HashMap (dict): tag -> frequency count for ranking
    - PriorityQueue (heapq): for ranking results by frequency
    
    Performance:
    - Build index: O(N*K) where N=items, K=avg keywords per item
    - Search: O(1) lookup + O(M log M) ranking where M=matched items
    
    Example:
        >>> service = SearchService()
        >>> service.build_index([item1, item2, item3])
        >>> results = service.search("algorithms", item_map)
        >>> print(f"Found {len(results)} matches")
    """
    
    def __init__(self):
        """Initialize search service with empty indexes."""
        self.keyword_to_items: Dict[str, Set[str]] = defaultdict(set)
        self.tag_frequency: Dict[str, int] = {}
        
        logger.debug("SearchService initialized")
    
    def build_index(self, items: List[Item]) -> None:
        """
        Build inverted index from items for fast keyword lookup.
        
        Creates two indexes:
        1. keyword_to_items: Maps each word/tag to set of item IDs
        2. tag_frequency: Counts how many items use each tag (for ranking)
        
        Args:
            items: List of items to index
        
        Time Complexity: O(N*K) where N=items, K=avg keywords per item
        Space Complexity: O(W) where W=unique words across all items
        
        Example:
            >>> service = SearchService()
            >>> items = [Item("DSP Notes", "Study", "pdf")]
            >>> items[0].add_tag("signals")
            >>> service.build_index(items)
        """
        # Clear existing indexes
        self.keyword_to_items.clear()
        self.tag_frequency.clear()
        
        logger.info(f"Building search index for {len(items)} items...")
        
        for item in items:
            # Index title words (split on whitespace)
            words = item.title.lower().split()
            for word in words:
                if word:  # Skip empty strings
                    self.keyword_to_items[word].add(item.id)
            
            # Index tags
            for tag in item.tags:
                tag_lower = tag.lower()
                
                # Add to keyword index
                self.keyword_to_items[tag_lower].add(item.id)
                
                # Update frequency count
                self.tag_frequency[tag_lower] = self.tag_frequency.get(tag_lower, 0) + 1
        
        total_keywords = len(self.keyword_to_items)
        total_tags = len(self.tag_frequency)
        
        logger.info(
            f"Index built: {total_keywords} unique keywords, "
            f"{total_tags} unique tags"
        )
    
    def search(self, query: str, item_map: Dict[str, Item]) -> List[str]:
        """
        Search for items matching query, ranked by tag frequency.
        
        PERFORMANCE DECISION: PriorityQueue for ranking search results
        
        Using heapq (PriorityQueue) because:
        1. Automatically maintains items sorted by frequency (max-heap behavior)
        2. O(log n) for insertion - acceptable for search result set
        3. O(1) for retrieving highest frequency item
        
        Alternative: Sort ArrayList afterwards would be O(n log n)
        PriorityQueue is more efficient for incremental result retrieval.
        
        Args:
            query: Search query string (single keyword)
            item_map: Dictionary mapping item IDs to Item objects
        
        Returns:
            List of item IDs, ranked by relevance (highest frequency first)
        
        Time Complexity: O(1) lookup + O(M log M) ranking where M=matched items
        
        Example:
            >>> item_map = {item.id: item for item in items}
            >>> results = service.search("algorithms", item_map)
            >>> for item_id in results:
            ...     print(item_map[item_id].title)
        """
        query_lower = query.lower().strip()
        
        if not query_lower:
            logger.warning("Empty search query")
            return []
        
        # O(1) lookup in HashMap
        matched_ids = self.keyword_to_items.get(query_lower, set())
        
        if not matched_ids:
            logger.debug(f"No matches for query: '{query}'")
            return []
        
        logger.debug(f"Found {len(matched_ids)} matches for: '{query}'")
        
        # Rank results by frequency (max-heap)
        ranked_results: List[ItemRank] = []
        
        for item_id in matched_ids:
            item = item_map.get(item_id)
            if item:
                # Calculate frequency score
                freq = self._calculate_frequency(item, query_lower)
                ranked_results.append(ItemRank(item_id, freq))
        
        # Use heapify for O(n) heap construction, then extract sorted
        heapq.heapify(ranked_results)
        
        # Extract results in order (highest frequency first)
        results = []
        while ranked_results:
            item_rank = heapq.heappop(ranked_results)
            results.append(item_rank.item_id)
        
        logger.debug(f"Returning {len(results)} ranked results")
        
        return results
    
    def _calculate_frequency(self, item: Item, query: str) -> int:
        """
        Calculate frequency score for ranking.
        
        Scores higher if query appears in tags with high usage frequency.
        
        Args:
            item: Item to calculate score for
            query: Search query (lowercase)
        
        Returns:
            Frequency score (higher = more relevant)
        """
        freq = 0
        
        for tag in item.tags:
            tag_lower = tag.lower()
            if query in tag_lower:
                # Add tag frequency from index (how many items use this tag)
                freq += self.tag_frequency.get(tag_lower, 1)
        
        return freq
    
    def get_keyword_index(self) -> Dict[str, Set[str]]:
        """
        Get the keyword index (for persistence).
        
        Returns:
            Dictionary mapping keywords to item ID sets
        """
        return dict(self.keyword_to_items)
    
    def get_tag_frequency(self) -> Dict[str, int]:
        """
        Get the tag frequency map (for persistence).
        
        Returns:
            Dictionary mapping tags to usage counts
        """
        return self.tag_frequency.copy()
    
    def get_popular_tags(self, count: int = 10) -> List[tuple]:
        """
        Get most popular tags by frequency.
        
        Args:
            count: Number of tags to return
        
        Returns:
            List of (tag, frequency) tuples, sorted by frequency descending
        
        Example:
            >>> popular = service.get_popular_tags(5)
            >>> for tag, freq in popular:
            ...     print(f"{tag}: {freq} items")
        """
        sorted_tags = sorted(
            self.tag_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_tags[:count]
    
    def suggest_keywords(self, prefix: str, max_results: int = 10) -> List[str]:
        """
        Get keyword suggestions matching prefix (simple prefix search).
        
        Args:
            prefix: Prefix to search for
            max_results: Maximum number of suggestions
        
        Returns:
            List of matching keywords
        
        Example:
            >>> suggestions = service.suggest_keywords("alg")
            >>> # Returns: ["algorithms", "algebra"]
        """
        prefix_lower = prefix.lower().strip()
        
        if not prefix_lower:
            return []
        
        # Simple prefix matching (O(n) - will be replaced by Trie later)
        matches = [
            keyword for keyword in self.keyword_to_items.keys()
            if keyword.startswith(prefix_lower)
        ]
        
        # Sort by number of items (more popular first)
        matches.sort(key=lambda k: len(self.keyword_to_items[k]), reverse=True)
        
        return matches[:max_results]

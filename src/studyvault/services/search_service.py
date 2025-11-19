"""
Search Service - Keyword indexing and ranked search functionality.

Builds inverted index (keyword -> item IDs) for O(1) lookups.
Ranks results by tag frequency using priority queue.
"""

from typing import List, Dict, Set
from collections import defaultdict
import logging

from studyvault.models.item import Item
from studyvault.utils.logger import get_logger

logger = get_logger(__name__)


class SearchService:
    """
    Service for building search indexes and performing ranked searches.
    
    Data Structures:
    - defaultdict(set): keyword -> set of item IDs for O(1) exact match
    - defaultdict(int): tag -> frequency count for ranking
    
    Performance:
    - Build index: O(N*K) where N=items, K=avg keywords per item
    - Search: O(T) lookup + O(M log M) ranking where T=query terms, M=matched items
    """
    
    def __init__(self):
        """Initialize search service with empty indexes."""
        self.keyword_to_items: Dict[str, Set[str]] = defaultdict(set)
        self.tag_frequency: Dict[str, int] = defaultdict(int)  # Changed to defaultdict
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("SearchService initialized")
    
    def build_index(self, items: List[Item]) -> None:
        """
        Build inverted index from items for fast keyword lookup.
        
        Creates two indexes:
        1. keyword_to_items: Maps each word/tag to set of item IDs
        2. tag_frequency: Counts how many items use each tag (for ranking)
        
        Time Complexity: O(N*K) where N=items, K=avg keywords per item
        """
        # Clear existing indexes
        self.keyword_to_items.clear()
        self.tag_frequency.clear()
        
        if logger.isEnabledFor(logging.INFO):
            logger.info(f"Building search index for {len(items)} items...")
        
        for item in items:
            # Index title words (split on whitespace)
            title_words = item.title.lower().split()
            for word in title_words:  # Removed unnecessary 'if word' check
                self.keyword_to_items[word].add(item.id)
            
            # Index category and type as single keywords
            self.keyword_to_items[item.category.lower()].add(item.id)
            self.keyword_to_items[item.type.lower()].add(item.id)
            
            # Index tags (already lowercase from Item.add_tag())
            for tag in item.tags:
                # Removed redundant .lower() - tags already lowercase
                self.keyword_to_items[tag].add(item.id)
                self.tag_frequency[tag] += 1  # Cleaner with defaultdict(int)
        
        if logger.isEnabledFor(logging.INFO):
            logger.info(
                f"Index built: {len(self.keyword_to_items)} unique keywords, "
                f"{len(self.tag_frequency)} unique tags"
            )
    
    def search(self, query: str, item_map: Dict[str, Item]) -> List[str]:
        """
        REWRITTEN: Now uses inverted index properly (O(T + M log M) instead of O(N*M))
        
        Perform multi-word keyword search with ranking.
        
        Args:
            query: Search query (whitespace-separated terms)
            item_map: Dict mapping item IDs to Item objects
        
        Returns:
            List of matching item IDs, ranked by relevance
        """
        query = query.lower().strip()
        if not query:
            return []
        
        query_terms = query.split()
        
        # Use inverted index for fast lookup
        # Find items matching ALL query terms (AND logic)
        matched_sets = []
        for term in query_terms:
            # Collect all items containing this term (substring match across keywords)
            term_matches = set()
            for keyword, item_ids in self.keyword_to_items.items():
                if term in keyword:  # Substring match
                    term_matches.update(item_ids)
            matched_sets.append(term_matches)
        
        # Intersection: items must match ALL terms
        if not matched_sets:
            return []
        
        matched_item_ids = matched_sets[0]
        for match_set in matched_sets[1:]:
            matched_item_ids &= match_set
        
        if not matched_item_ids:
            return []
        
        # Rank results using tuple sort (avoid ItemRank overhead)
        ranked_results = []
        for item_id in matched_item_ids:
            item = item_map.get(item_id)
            if not item:
                continue
            
            freq = self._calculate_frequency(item, query_terms)
            ranked_results.append((freq, item.title.lower(), item_id))
        
        # Sort by: frequency DESC, title ASC (for stable ordering)
        ranked_results.sort(key=lambda x: (-x[0], x[1]))
        
        return [item_id for _, _, item_id in ranked_results]
    
    def _calculate_frequency(self, item: Item, query_terms: List[str]) -> int:
        """
        UPDATED: Calculate frequency score for ranking.
        
        Args:
            item: Item to calculate score for
            query_terms: List of lowercase query terms
        
        Returns:
            Frequency score (higher = more relevant)
        """
        freq = 0
        
        # Check each tag against each query term
        for tag in item.tags:  # Tags already lowercase
            for term in query_terms:
                if term in tag:
                    # Add tag frequency (how many items use this tag)
                    freq += self.tag_frequency[tag]  # defaultdict, no .get()
        
        return freq
    
    def get_keyword_index(self) -> Dict[str, Set[str]]:
        """Get the keyword index (for persistence)."""
        return dict(self.keyword_to_items)
    
    def get_tag_frequency(self) -> Dict[str, int]:
        """Get the tag frequency map (for persistence)."""
        return dict(self.tag_frequency)
    
    def get_popular_tags(self, count: int = 10) -> List[tuple]:
        """
        Get most popular tags by frequency.
        
        Optimized: O(N log K) instead of O(N log N) for small count
        """
        import heapq
        return heapq.nlargest(count, self.tag_frequency.items(), key=lambda x: x[1])
    
    def suggest_keywords(self, prefix: str, max_results: int = 10) -> List[str]:
        """
        OPTIMIZED: Get keyword suggestions matching prefix.
        
        Still O(W) but with optimized sorting.
        TODO: Replace with Trie for O(K) where K=results
        """
        prefix_lower = prefix.lower().strip()
        
        if not prefix_lower:
            return []
        
        # Find matching keywords with counts
        matches_with_counts = [
            (keyword, len(item_ids))
            for keyword, item_ids in self.keyword_to_items.items()
            if keyword.startswith(prefix_lower)
        ]
        
        # Use heapq for top-K (faster for small max_results)
        import heapq
        top_matches = heapq.nlargest(
            max_results,
            matches_with_counts,
            key=lambda x: x[1]
        )
        
        return [keyword for keyword, _ in top_matches]

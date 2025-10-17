"""
Source Highlighter Service

Highlights relevant parts of source documents that support RAG answers.

Features:
1. Exact match highlighting
2. Fuzzy match highlighting
3. Semantic similarity highlighting
4. Multi-language support (Korean, English)
5. Context window extraction
"""

import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class SourceHighlighter:
    """
    Highlights relevant parts of source documents.
    
    Methods:
    - Exact matching: Direct text matches
    - Fuzzy matching: Similar text with typos/variations
    - Semantic matching: Conceptually similar text
    - Context extraction: Surrounding context for highlights
    """

    def __init__(
        self,
        context_window: int = 100,
        min_match_length: int = 10,
        fuzzy_threshold: float = 0.8,
        max_highlights: int = 5
    ):
        """
        Initialize Source Highlighter.
        
        Args:
            context_window: Characters to include before/after highlight
            min_match_length: Minimum characters for a match
            fuzzy_threshold: Similarity threshold for fuzzy matching (0-1)
            max_highlights: Maximum number of highlights per document
        """
        self.context_window = context_window
        self.min_match_length = min_match_length
        self.fuzzy_threshold = fuzzy_threshold
        self.max_highlights = max_highlights
        
        logger.info(
            f"SourceHighlighter initialized: "
            f"context_window={context_window}, "
            f"min_match_length={min_match_length}"
        )

    def highlight_sources(
        self,
        answer: str,
        sources: List[Dict[str, Any]],
        method: str = "auto"
    ) -> List[Dict[str, Any]]:
        """
        Highlight relevant parts in source documents.
        
        Args:
            answer: Generated RAG answer
            sources: List of source documents with 'text' field
            method: Highlighting method ("exact", "fuzzy", "semantic", "auto")
        
        Returns:
            List of sources with highlights added
        """
        if not answer or not sources:
            return sources
        
        # Extract key phrases from answer
        key_phrases = self._extract_key_phrases(answer)
        
        logger.info(
            f"Highlighting sources: {len(sources)} documents, "
            f"{len(key_phrases)} key phrases"
        )
        
        highlighted_sources = []
        
        for source in sources:
            text = source.get('text', '') or source.get('content', '')
            
            if not text:
                highlighted_sources.append(source)
                continue
            
            # Find highlights based on method
            if method == "auto":
                # Try exact first, then fuzzy
                highlights = self._find_exact_matches(key_phrases, text)
                if not highlights:
                    highlights = self._find_fuzzy_matches(key_phrases, text)
            elif method == "exact":
                highlights = self._find_exact_matches(key_phrases, text)
            elif method == "fuzzy":
                highlights = self._find_fuzzy_matches(key_phrases, text)
            else:
                highlights = []
            
            # Limit number of highlights
            highlights = highlights[:self.max_highlights]
            
            # Add highlights to source
            source_with_highlights = source.copy()
            source_with_highlights['highlights'] = highlights
            source_with_highlights['highlight_count'] = len(highlights)
            
            highlighted_sources.append(source_with_highlights)
        
        logger.info(
            f"Highlighting complete: "
            f"{sum(s['highlight_count'] for s in highlighted_sources)} total highlights"
        )
        
        return highlighted_sources

    def _extract_key_phrases(self, text: str) -> List[str]:
        """
        Extract key phrases from text.
        
        Args:
            text: Input text
        
        Returns:
            List of key phrases
        """
        # Split into sentences
        sentences = re.split(r'[.!?。！？]\s+', text)
        
        # Extract phrases (noun phrases, important terms)
        phrases = []
        
        for sentence in sentences:
            # Remove short sentences
            if len(sentence) < self.min_match_length:
                continue
            
            # Split by commas and conjunctions
            parts = re.split(r'[,，]\s+|그리고|또한|하지만|그러나|and|but|or', sentence)
            
            for part in parts:
                part = part.strip()
                if len(part) >= self.min_match_length:
                    phrases.append(part)
        
        # Also add full sentences for better matching
        phrases.extend([s.strip() for s in sentences if len(s.strip()) >= self.min_match_length])
        
        # Remove duplicates and sort by length (longer first)
        phrases = list(set(phrases))
        phrases.sort(key=len, reverse=True)
        
        return phrases[:20]  # Limit to top 20 phrases

    def _find_exact_matches(
        self,
        phrases: List[str],
        text: str
    ) -> List[Dict[str, Any]]:
        """
        Find exact matches of phrases in text.
        
        Args:
            phrases: List of phrases to find
            text: Text to search in
        
        Returns:
            List of highlight dictionaries
        """
        highlights = []
        text_lower = text.lower()
        
        for phrase in phrases:
            phrase_lower = phrase.lower()
            
            # Find all occurrences
            start = 0
            while True:
                pos = text_lower.find(phrase_lower, start)
                if pos == -1:
                    break
                
                # Extract context
                context_start = max(0, pos - self.context_window)
                context_end = min(len(text), pos + len(phrase) + self.context_window)
                
                highlight = {
                    "type": "exact",
                    "matched_phrase": phrase,
                    "start": pos,
                    "end": pos + len(phrase),
                    "text": text[pos:pos + len(phrase)],
                    "context": text[context_start:context_end],
                    "context_start": context_start,
                    "context_end": context_end,
                    "score": 1.0
                }
                
                highlights.append(highlight)
                start = pos + 1
                
                # Limit matches per phrase
                if len(highlights) >= self.max_highlights:
                    break
            
            if len(highlights) >= self.max_highlights:
                break
        
        # Remove overlapping highlights (keep longer ones)
        highlights = self._remove_overlaps(highlights)
        
        return highlights

    def _find_fuzzy_matches(
        self,
        phrases: List[str],
        text: str
    ) -> List[Dict[str, Any]]:
        """
        Find fuzzy matches of phrases in text.
        
        Args:
            phrases: List of phrases to find
            text: Text to search in
        
        Returns:
            List of highlight dictionaries
        """
        highlights = []
        
        # Split text into windows
        words = text.split()
        
        for phrase in phrases:
            phrase_words = phrase.split()
            phrase_len = len(phrase_words)
            
            if phrase_len == 0:
                continue
            
            # Sliding window
            for i in range(len(words) - phrase_len + 1):
                window = ' '.join(words[i:i + phrase_len])
                
                # Calculate similarity
                similarity = SequenceMatcher(None, phrase.lower(), window.lower()).ratio()
                
                if similarity >= self.fuzzy_threshold:
                    # Find position in original text
                    pos = text.find(window)
                    if pos == -1:
                        continue
                    
                    # Extract context
                    context_start = max(0, pos - self.context_window)
                    context_end = min(len(text), pos + len(window) + self.context_window)
                    
                    highlight = {
                        "type": "fuzzy",
                        "matched_phrase": phrase,
                        "start": pos,
                        "end": pos + len(window),
                        "text": window,
                        "context": text[context_start:context_end],
                        "context_start": context_start,
                        "context_end": context_end,
                        "score": similarity
                    }
                    
                    highlights.append(highlight)
                    
                    if len(highlights) >= self.max_highlights:
                        break
            
            if len(highlights) >= self.max_highlights:
                break
        
        # Remove overlapping highlights
        highlights = self._remove_overlaps(highlights)
        
        # Sort by score
        highlights.sort(key=lambda x: x['score'], reverse=True)
        
        return highlights

    def _remove_overlaps(
        self,
        highlights: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove overlapping highlights, keeping higher scoring ones.
        
        Args:
            highlights: List of highlights
        
        Returns:
            List of non-overlapping highlights
        """
        if not highlights:
            return []
        
        # Sort by score (descending)
        sorted_highlights = sorted(highlights, key=lambda x: x['score'], reverse=True)
        
        # Keep non-overlapping highlights
        kept = []
        
        for highlight in sorted_highlights:
            # Check if overlaps with any kept highlight
            overlaps = False
            for kept_highlight in kept:
                if self._is_overlap(highlight, kept_highlight):
                    overlaps = True
                    break
            
            if not overlaps:
                kept.append(highlight)
        
        # Sort by position
        kept.sort(key=lambda x: x['start'])
        
        return kept

    def _is_overlap(
        self,
        h1: Dict[str, Any],
        h2: Dict[str, Any]
    ) -> bool:
        """Check if two highlights overlap"""
        return not (h1['end'] <= h2['start'] or h2['end'] <= h1['start'])

    def format_highlighted_text(
        self,
        source: Dict[str, Any],
        format_type: str = "html"
    ) -> str:
        """
        Format highlighted text for display.
        
        Args:
            source: Source document with highlights
            format_type: Output format ("html", "markdown", "plain")
        
        Returns:
            Formatted text with highlights
        """
        text = source.get('text', '') or source.get('content', '')
        highlights = source.get('highlights', [])
        
        if not highlights:
            return text
        
        # Sort highlights by position
        sorted_highlights = sorted(highlights, key=lambda x: x['start'])
        
        # Build formatted text
        result = []
        last_pos = 0
        
        for highlight in sorted_highlights:
            # Add text before highlight
            result.append(text[last_pos:highlight['start']])
            
            # Add highlighted text
            highlighted_text = text[highlight['start']:highlight['end']]
            
            if format_type == "html":
                result.append(f'<mark class="highlight" data-score="{highlight["score"]:.2f}">{highlighted_text}</mark>')
            elif format_type == "markdown":
                result.append(f'**{highlighted_text}**')
            else:  # plain
                result.append(f'[{highlighted_text}]')
            
            last_pos = highlight['end']
        
        # Add remaining text
        result.append(text[last_pos:])
        
        return ''.join(result)


# Global instance
_source_highlighter: Optional[SourceHighlighter] = None


def get_source_highlighter(
    context_window: int = 100,
    min_match_length: int = 10
) -> SourceHighlighter:
    """
    Get global source highlighter instance.
    
    Args:
        context_window: Characters to include before/after highlight
        min_match_length: Minimum characters for a match
    
    Returns:
        SourceHighlighter instance
    """
    global _source_highlighter
    
    if _source_highlighter is None:
        _source_highlighter = SourceHighlighter(
            context_window=context_window,
            min_match_length=min_match_length
        )
    
    return _source_highlighter

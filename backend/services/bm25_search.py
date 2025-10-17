# BM25 Keyword Search Service
import math
import logging
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
import re

logger = logging.getLogger(__name__)


class BM25:
    """
    BM25 (Best Matching 25) ranking function for keyword-based search.

    Combines term frequency (TF) and inverse document frequency (IDF)
    with document length normalization.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 parameters.

        Args:
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
        """
        self.k1 = k1
        self.b = b
        self.corpus: List[List[str]] = []
        self.doc_ids: List[str] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.num_docs: int = 0

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Convert to lowercase and split on non-alphanumeric
        tokens = re.findall(r"\b\w+\b", text.lower())
        return tokens

    def fit(self, corpus: List[str], doc_ids: List[str]):
        """
        Build BM25 index from corpus.

        Args:
            corpus: List of document texts
            doc_ids: List of document IDs
        """
        self.corpus = [self.tokenize(doc) for doc in corpus]
        self.doc_ids = doc_ids
        self.num_docs = len(corpus)

        # Calculate document lengths
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avg_doc_length = (
            sum(self.doc_lengths) / self.num_docs if self.num_docs > 0 else 0
        )

        # Calculate document frequencies
        self.doc_freqs = defaultdict(int)
        for doc in self.corpus:
            unique_terms = set(doc)
            for term in unique_terms:
                self.doc_freqs[term] += 1

        # Calculate IDF scores
        self.idf = {}
        for term, freq in self.doc_freqs.items():
            # IDF = log((N - df + 0.5) / (df + 0.5) + 1)
            self.idf[term] = math.log((self.num_docs - freq + 0.5) / (freq + 0.5) + 1.0)

        logger.info(
            f"BM25 index built: {self.num_docs} documents, "
            f"{len(self.idf)} unique terms"
        )

    def score(self, query: str, doc_idx: int) -> float:
        """
        Calculate BM25 score for a query-document pair.

        Args:
            query: Query text
            doc_idx: Document index

        Returns:
            BM25 score
        """
        query_terms = self.tokenize(query)
        doc = self.corpus[doc_idx]
        doc_length = self.doc_lengths[doc_idx]

        # Count term frequencies in document
        term_freqs = Counter(doc)

        score = 0.0
        for term in query_terms:
            if term not in self.idf:
                continue

            tf = term_freqs.get(term, 0)
            idf = self.idf[term]

            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * (doc_length / self.avg_doc_length)
            )

            score += idf * (numerator / denominator)

        return score

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Search for top-k documents matching query.

        Args:
            query: Query text
            top_k: Number of results to return

        Returns:
            List of (doc_id, score) tuples, sorted by score descending
        """
        if self.num_docs == 0:
            return []

        # Calculate scores for all documents
        scores = []
        for idx in range(self.num_docs):
            score = self.score(query, idx)
            if score > 0:
                scores.append((self.doc_ids[idx], score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_k]


class BM25SearchService:
    """Service for BM25-based keyword search"""

    def __init__(self):
        self.bm25: BM25 = None
        self.indexed = False

    async def index_documents(self, documents: List[Dict[str, str]]):
        """
        Index documents for BM25 search.

        Args:
            documents: List of documents with 'id' and 'content' keys
        """
        if not documents:
            logger.warning("No documents to index")
            return

        corpus = [doc["content"] for doc in documents]
        doc_ids = [doc["id"] for doc in documents]

        self.bm25 = BM25()
        self.bm25.fit(corpus, doc_ids)
        self.indexed = True

        logger.info(f"Indexed {len(documents)} documents for BM25 search")

    async def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Search documents using BM25.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (doc_id, score) tuples
        """
        if not self.indexed or self.bm25 is None:
            logger.warning("BM25 index not built, returning empty results")
            return []

        results = self.bm25.search(query, top_k)

        logger.info(
            f"BM25 search completed: query='{query}', " f"results={len(results)}"
        )

        return results


# Global BM25 service instance
_bm25_service: BM25SearchService = None


def get_bm25_service() -> BM25SearchService:
    """Get global BM25 service instance"""
    global _bm25_service
    if _bm25_service is None:
        _bm25_service = BM25SearchService()
    return _bm25_service

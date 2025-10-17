# Active Learning - Learn from User Feedback
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class FeedbackType:
    """Types of user feedback"""

    POSITIVE = "positive"  # Helpful answer
    NEGATIVE = "negative"  # Not helpful
    PARTIAL = "partial"  # Partially helpful
    IRRELEVANT = "irrelevant"  # Irrelevant results


class ActiveLearningService:
    """
    Active Learning system that improves from user feedback.

    Features:
    - Collect user feedback on search results
    - Identify problematic queries
    - Fine-tune embeddings
    - Update reranking models
    - Continuous improvement

    Benefits:
    - System gets better over time
    - Personalized to user needs
    - Automatic quality improvement
    """

    def __init__(self, embedding_service, redis_client: Optional[redis.Redis] = None):
        self.embedding_service = embedding_service
        self.redis_client = redis_client

        # Feedback storage
        self.feedback_data: List[Dict[str, Any]] = []
        self.query_feedback_map = defaultdict(list)

        # Learning statistics
        self.stats = {
            "total_feedback": 0,
            "positive_feedback": 0,
            "negative_feedback": 0,
            "learning_iterations": 0,
            "avg_improvement": 0.0,
        }

    async def collect_feedback(
        self,
        query: str,
        results: List[Dict[str, Any]],
        feedback_type: str,
        result_ids: Optional[List[str]] = None,
        user_comment: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Collect user feedback on search results.

        Args:
            query: Original query
            results: Search results shown to user
            feedback_type: Type of feedback (positive/negative/partial/irrelevant)
            result_ids: IDs of results user interacted with
            user_comment: Optional user comment
            user_id: Optional user identifier

        Returns:
            Feedback record
        """
        try:
            feedback = {
                "query": query,
                "feedback_type": feedback_type,
                "result_ids": result_ids or [],
                "result_count": len(results),
                "user_comment": user_comment,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "results": results[:5],  # Store top 5 for analysis
            }

            # Store feedback
            self.feedback_data.append(feedback)
            self.query_feedback_map[query].append(feedback)

            # Update statistics
            self.stats["total_feedback"] += 1
            if feedback_type == FeedbackType.POSITIVE:
                self.stats["positive_feedback"] += 1
            elif feedback_type == FeedbackType.NEGATIVE:
                self.stats["negative_feedback"] += 1

            # Store in Redis if available
            if self.redis_client:
                await self._store_feedback_redis(feedback)

            logger.info(
                f"Collected {feedback_type} feedback for query: {query[:50]}..."
            )

            # Check if we should trigger learning
            if self.stats["total_feedback"] % 100 == 0:
                logger.info("Triggering active learning update...")
                await self.learn_from_feedback()

            return feedback

        except Exception as e:
            logger.error(f"Failed to collect feedback: {e}")
            return {}

    async def learn_from_feedback(self) -> Dict[str, Any]:
        """
        Learn from collected feedback to improve the system.

        Returns:
            Learning results and improvements
        """
        try:
            logger.info(f"Learning from {len(self.feedback_data)} feedback entries...")

            # 1. Identify problematic queries
            problematic_queries = self._identify_problematic_queries()

            # 2. Extract positive and negative pairs
            positive_pairs, negative_pairs = self._extract_training_pairs()

            # 3. Generate improvement suggestions
            improvements = {
                "problematic_queries": problematic_queries,
                "positive_pairs_count": len(positive_pairs),
                "negative_pairs_count": len(negative_pairs),
                "suggestions": [],
            }

            # 4. Analyze patterns
            patterns = self._analyze_feedback_patterns()
            improvements["patterns"] = patterns

            # 5. Generate reranking signals
            reranking_signals = self._generate_reranking_signals()
            improvements["reranking_signals"] = reranking_signals

            self.stats["learning_iterations"] += 1

            logger.info(
                f"Learning complete: {len(problematic_queries)} problematic queries, "
                f"{len(positive_pairs)} positive pairs, {len(negative_pairs)} negative pairs"
            )

            return improvements

        except Exception as e:
            logger.error(f"Learning from feedback failed: {e}")
            return {}

    def _identify_problematic_queries(self) -> List[Dict[str, Any]]:
        """Identify queries with consistently negative feedback"""
        problematic = []

        for query, feedbacks in self.query_feedback_map.items():
            if len(feedbacks) < 2:
                continue

            negative_count = sum(
                1
                for f in feedbacks
                if f["feedback_type"]
                in [FeedbackType.NEGATIVE, FeedbackType.IRRELEVANT]
            )

            negative_rate = negative_count / len(feedbacks)

            if negative_rate > 0.6:  # More than 60% negative
                problematic.append(
                    {
                        "query": query,
                        "feedback_count": len(feedbacks),
                        "negative_rate": negative_rate,
                        "avg_result_count": np.mean(
                            [f["result_count"] for f in feedbacks]
                        ),
                    }
                )

        # Sort by negative rate
        problematic.sort(key=lambda x: x["negative_rate"], reverse=True)

        return problematic[:20]  # Top 20 problematic queries

    def _extract_training_pairs(self) -> Tuple[List[Tuple], List[Tuple]]:
        """Extract positive and negative query-document pairs"""
        positive_pairs = []
        negative_pairs = []

        for feedback in self.feedback_data:
            query = feedback["query"]
            results = feedback["results"]
            feedback_type = feedback["feedback_type"]
            result_ids = feedback.get("result_ids", [])

            if feedback_type == FeedbackType.POSITIVE:
                # Positive pairs: query + clicked results
                for result_id in result_ids:
                    for result in results:
                        if (
                            result.get("chunk_id") == result_id
                            or result.get("id") == result_id
                        ):
                            positive_pairs.append((query, result.get("text", "")))

            elif feedback_type == FeedbackType.NEGATIVE:
                # Negative pairs: query + shown but not clicked results
                for result in results:
                    result_id = result.get("chunk_id") or result.get("id")
                    if result_id not in result_ids:
                        negative_pairs.append((query, result.get("text", "")))

        return positive_pairs, negative_pairs

    def _analyze_feedback_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in feedback"""
        patterns = {
            "common_negative_queries": [],
            "low_result_queries": [],
            "high_performing_queries": [],
        }

        # Group by query characteristics
        query_stats = defaultdict(lambda: {"positive": 0, "negative": 0, "total": 0})

        for feedback in self.feedback_data:
            query = feedback["query"]
            query_length = len(query.split())

            # Categorize by length
            if query_length < 5:
                category = "short"
            elif query_length < 15:
                category = "medium"
            else:
                category = "long"

            query_stats[category]["total"] += 1

            if feedback["feedback_type"] == FeedbackType.POSITIVE:
                query_stats[category]["positive"] += 1
            elif feedback["feedback_type"] == FeedbackType.NEGATIVE:
                query_stats[category]["negative"] += 1

        # Calculate success rates
        for category, stats in query_stats.items():
            if stats["total"] > 0:
                success_rate = stats["positive"] / stats["total"]
                patterns[f"{category}_query_success_rate"] = success_rate

        return patterns

    def _generate_reranking_signals(self) -> Dict[str, float]:
        """Generate signals for reranking based on feedback"""
        signals = {}

        # Document popularity (clicked documents)
        doc_clicks = defaultdict(int)
        doc_shows = defaultdict(int)

        for feedback in self.feedback_data:
            result_ids = feedback.get("result_ids", [])

            for result in feedback["results"]:
                doc_id = result.get("chunk_id") or result.get("id")
                doc_shows[doc_id] += 1

                if doc_id in result_ids:
                    doc_clicks[doc_id] += 1

        # Calculate CTR (Click-Through Rate)
        for doc_id, shows in doc_shows.items():
            if shows > 0:
                ctr = doc_clicks[doc_id] / shows
                signals[doc_id] = ctr

        return signals

    async def _store_feedback_redis(self, feedback: Dict[str, Any]):
        """Store feedback in Redis"""
        try:
            import json

            key = f"feedback:{feedback['timestamp']}"
            value = json.dumps(feedback)
            await self.redis_client.setex(key, 86400 * 30, value)  # 30 days
        except Exception as e:
            logger.debug(f"Redis storage failed: {e}")

    async def get_query_suggestions(self, query: str, top_k: int = 5) -> List[str]:
        """
        Get query suggestions based on successful similar queries.

        Args:
            query: User's query
            top_k: Number of suggestions

        Returns:
            List of suggested queries
        """
        try:
            # Find similar successful queries
            query_embedding = await self.embedding_service.embed(query)

            successful_queries = [
                f["query"]
                for f in self.feedback_data
                if f["feedback_type"] == FeedbackType.POSITIVE
            ]

            if not successful_queries:
                return []

            # Embed successful queries
            successful_embeddings = await self.embedding_service.embed_batch(
                successful_queries
            )

            # Calculate similarities
            from sentence_transformers import util
            import torch

            query_tensor = torch.tensor(query_embedding).unsqueeze(0)
            success_tensors = torch.tensor(successful_embeddings)

            similarities = util.cos_sim(query_tensor, success_tensors)[0]

            # Get top similar queries
            top_indices = torch.topk(
                similarities, min(top_k, len(similarities))
            ).indices

            suggestions = [successful_queries[i] for i in top_indices]

            return suggestions

        except Exception as e:
            logger.error(f"Query suggestion failed: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get active learning statistics"""
        if self.stats["total_feedback"] > 0:
            positive_rate = (
                self.stats["positive_feedback"] / self.stats["total_feedback"]
            )
        else:
            positive_rate = 0.0

        return {
            **self.stats,
            "positive_rate": positive_rate,
            "feedback_data_size": len(self.feedback_data),
        }

    async def export_training_data(
        self, output_file: str = "training_data.jsonl"
    ) -> int:
        """
        Export feedback data for model fine-tuning.

        Args:
            output_file: Output file path

        Returns:
            Number of exported records
        """
        try:
            import json

            positive_pairs, negative_pairs = self._extract_training_pairs()

            with open(output_file, "w", encoding="utf-8") as f:
                # Export positive pairs
                for query, text in positive_pairs:
                    record = {"query": query, "text": text, "label": 1}
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

                # Export negative pairs
                for query, text in negative_pairs:
                    record = {"query": query, "text": text, "label": 0}
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

            total_records = len(positive_pairs) + len(negative_pairs)
            logger.info(f"Exported {total_records} training records to {output_file}")

            return total_records

        except Exception as e:
            logger.error(f"Training data export failed: {e}")
            return 0


def create_active_learning_service(
    embedding_service, redis_client: Optional[redis.Redis] = None
) -> ActiveLearningService:
    """Factory function"""
    return ActiveLearningService(embedding_service, redis_client)

# Knowledge Graph Service for Document Relationships
import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Extracted entity"""

    name: str
    type: str  # person, organization, concept, technology, etc.
    mentions: int
    documents: Set[str]


@dataclass
class Relationship:
    """Relationship between entities"""

    source: str
    target: str
    relation_type: str  # related_to, part_of, uses, compares, etc.
    weight: float
    documents: Set[str]


class KnowledgeGraph:
    """
    Knowledge Graph for document relationships and entity extraction.

    Features:
    - Entity extraction from documents
    - Relationship mapping between entities
    - Document similarity based on shared entities
    - Graph-based reasoning and traversal
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []
        self.doc_entities: Dict[str, Set[str]] = defaultdict(set)

    def extract_entities(self, text: str, doc_id: str) -> List[Entity]:
        """
        Extract entities from text.

        Simple implementation - can be enhanced with NER models.
        """
        entities = []

        # Simple pattern-based extraction
        # Technology names (capitalized words)
        import re

        tech_pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"
        matches = re.findall(tech_pattern, text)

        for match in set(matches):
            if len(match) > 2:  # Filter short matches
                entity_name = match.lower()

                if entity_name not in self.entities:
                    self.entities[entity_name] = Entity(
                        name=entity_name, type="concept", mentions=0, documents=set()
                    )

                self.entities[entity_name].mentions += 1
                self.entities[entity_name].documents.add(doc_id)
                self.doc_entities[doc_id].add(entity_name)

                entities.append(self.entities[entity_name])

        return entities

    def add_document(self, doc_id: str, text: str, metadata: Dict = None):
        """Add document to knowledge graph"""
        # Extract entities
        entities = self.extract_entities(text, doc_id)

        # Add document node
        self.graph.add_node(doc_id, type="document", metadata=metadata or {})

        # Add entity nodes and edges
        for entity in entities:
            if not self.graph.has_node(entity.name):
                self.graph.add_node(entity.name, type="entity", entity_type=entity.type)

            # Connect document to entity
            self.graph.add_edge(doc_id, entity.name, relation="contains")

        logger.info(f"Added document {doc_id} with {len(entities)} entities")

    def find_related_documents(
        self, doc_id: str, max_results: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find documents related to given document based on shared entities.

        Returns:
            List of (doc_id, similarity_score) tuples
        """
        if doc_id not in self.doc_entities:
            return []

        source_entities = self.doc_entities[doc_id]

        # Calculate similarity with other documents
        similarities = []
        for other_doc_id, other_entities in self.doc_entities.items():
            if other_doc_id == doc_id:
                continue

            # Jaccard similarity
            intersection = len(source_entities & other_entities)
            union = len(source_entities | other_entities)

            if union > 0:
                similarity = intersection / union
                if similarity > 0:
                    similarities.append((other_doc_id, similarity))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:max_results]

    def find_entity_connections(self, entity: str, max_depth: int = 2) -> List[str]:
        """Find entities connected to given entity"""
        if entity not in self.graph:
            return []

        # BFS to find connected entities
        connected = []
        visited = set()
        queue = [(entity, 0)]

        while queue:
            current, depth = queue.pop(0)

            if current in visited or depth > max_depth:
                continue

            visited.add(current)

            if current != entity and self.graph.nodes[current].get("type") == "entity":
                connected.append(current)

            # Add neighbors
            for neighbor in self.graph.neighbors(current):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))

        return connected

    def get_graph_stats(self) -> Dict:
        """Get knowledge graph statistics"""
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "total_entities": len(self.entities),
            "total_documents": len(self.doc_entities),
            "avg_entities_per_doc": (
                sum(len(e) for e in self.doc_entities.values()) / len(self.doc_entities)
                if self.doc_entities
                else 0
            ),
        }


# Global knowledge graph instance
_knowledge_graph: Optional[KnowledgeGraph] = None


def get_knowledge_graph() -> KnowledgeGraph:
    """Get global knowledge graph instance"""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph()
    return _knowledge_graph

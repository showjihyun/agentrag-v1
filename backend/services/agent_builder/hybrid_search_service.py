"""
Hybrid Search Service

Combines vector search with knowledge graph search for enhanced RAG capabilities.
Provides unified search interface that can leverage both semantic similarity and
structured knowledge relationships.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session

from backend.db.models.agent_builder import Knowledgebase
from backend.services.agent_builder.knowledge_graph_service import KnowledgeGraphService
from backend.agents.vector_search import VectorSearchAgent
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


class HybridSearchService:
    """Service for hybrid vector + knowledge graph search."""
    
    def __init__(self, db: Session, vector_agent: Optional[VectorSearchAgent] = None):
        self.db = db
        self.kg_service = KnowledgeGraphService(db)
        
        # Initialize vector agent if not provided
        if vector_agent is None:
            try:
                # Try to initialize VectorSearchAgent with available services
                from backend.core.dependencies_optimized import get_milvus_manager, get_embedding_service
                
                try:
                    milvus_manager = get_milvus_manager()
                    embedding_service = get_embedding_service()
                    
                    self.vector_agent = VectorSearchAgent(
                        milvus_manager=milvus_manager,
                        embedding_service=embedding_service,
                    )
                    logger.info("✅ VectorSearchAgent initialized successfully with Milvus")
                except Exception as init_error:
                    logger.warning(f"Failed to initialize Milvus/Embedding services: {init_error}")
                    # Try alternative initialization
                    try:
                        from backend.services.embedding_service import get_embedding_service as get_emb_svc
                        embedding_service = get_emb_svc()
                        
                        self.vector_agent = VectorSearchAgent(
                            embedding_service=embedding_service,
                        )
                        logger.info("✅ VectorSearchAgent initialized with embedding service only")
                    except Exception as fallback_error:
                        logger.warning(f"Failed to initialize VectorSearchAgent fallback: {fallback_error}")
                        self.vector_agent = None
                        
            except Exception as e:
                logger.warning(f"❌ Failed to initialize VectorSearchAgent: {e}")
                self.vector_agent = None
        else:
            self.vector_agent = vector_agent
            logger.info("✅ VectorSearchAgent provided externally")
    
    async def search(
        self,
        knowledgebase_id: str,
        query: str,
        limit: int = 10,
        search_strategy: str = "hybrid",
        vector_weight: float = 0.7,
        graph_weight: float = 0.3,
        include_entities: bool = True,
        include_relationships: bool = True,
        entity_expansion_depth: int = 1,
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining vector and knowledge graph results.
        
        Args:
            knowledgebase_id: ID of the knowledgebase to search
            query: Search query
            limit: Maximum number of results to return
            search_strategy: 'vector', 'graph', or 'hybrid'
            vector_weight: Weight for vector search results (0.0-1.0)
            graph_weight: Weight for graph search results (0.0-1.0)
            include_entities: Whether to include entity matches
            include_relationships: Whether to include relationship matches
            entity_expansion_depth: Depth for entity relationship expansion
            
        Returns:
            Dictionary containing search results and metadata
        """
        
        # Get knowledgebase configuration
        kb = self.db.query(Knowledgebase).filter(Knowledgebase.id == knowledgebase_id).first()
        if not kb:
            raise ValueError("Knowledgebase not found")
        
        # Determine search strategy
        if search_strategy == "auto":
            search_strategy = kb.search_strategy or "vector"
        
        # Normalize weights
        total_weight = vector_weight + graph_weight
        if total_weight > 0:
            vector_weight = vector_weight / total_weight
            graph_weight = graph_weight / total_weight
        else:
            vector_weight = 0.7
            graph_weight = 0.3
        
        results = {
            "documents": [],
            "entities": [],
            "relationships": [],
            "metadata": {
                "query": query,
                "strategy": search_strategy,
                "vector_weight": vector_weight,
                "graph_weight": graph_weight,
                "total_results": 0,
            }
        }
        
        try:
            if search_strategy == "vector":
                # Vector search only
                vector_results = await self._vector_search(knowledgebase_id, query, limit)
                results["documents"] = vector_results
                results["metadata"]["total_results"] = len(vector_results)
                
            elif search_strategy == "graph" and kb.kg_enabled:
                # Knowledge graph search only
                kg_results = await self._knowledge_graph_search(
                    knowledgebase_id, query, limit, include_entities, include_relationships
                )
                results.update(kg_results)
                results["metadata"]["total_results"] = (
                    len(results["entities"]) + len(results["relationships"])
                )
                
            elif search_strategy == "hybrid" and kb.kg_enabled:
                # Hybrid search
                hybrid_results = await self._hybrid_search(
                    knowledgebase_id, query, limit, vector_weight, graph_weight,
                    include_entities, include_relationships, entity_expansion_depth
                )
                results.update(hybrid_results)
                results["metadata"]["total_results"] = (
                    len(results["documents"]) + len(results["entities"]) + len(results["relationships"])
                )
                
            else:
                # Fallback to vector search
                vector_results = await self._vector_search(knowledgebase_id, query, limit)
                results["documents"] = vector_results
                results["metadata"]["total_results"] = len(vector_results)
                results["metadata"]["fallback"] = "Vector search (KG not available)"
        
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            # Fallback to vector search on error
            try:
                vector_results = await self._vector_search(knowledgebase_id, query, limit)
                results["documents"] = vector_results
                results["metadata"]["total_results"] = len(vector_results)
                results["metadata"]["error"] = str(e)
                results["metadata"]["fallback"] = "Vector search (error in hybrid)"
            except Exception as fallback_error:
                logger.error(f"Fallback vector search also failed: {str(fallback_error)}")
                results["metadata"]["error"] = f"Hybrid: {str(e)}, Vector: {str(fallback_error)}"
        
        return results
    
    async def _vector_search(
        self,
        knowledgebase_id: str,
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Perform vector search using KB-specific collection and embedding model."""

        try:
            # Get KB to access its collection and embedding settings
            kb = self.db.query(Knowledgebase).filter(Knowledgebase.id == knowledgebase_id).first()
            if not kb:
                logger.warning(f"Knowledgebase {knowledgebase_id} not found")
                return []

            # Import required services
            from backend.services.embedding import EmbeddingService
            from backend.services.milvus import MilvusManager

            # Use KB's embedding model
            embedding_model = kb.embedding_model or "jhgan/ko-sroberta-multitask"
            embedding_service = EmbeddingService(model_name=embedding_model)

            # Get embedding dimension from KB or service
            embedding_dim = getattr(kb, 'embedding_dimension', None) or embedding_service.dimension

            # Create MilvusManager for KB's specific collection
            milvus_manager = MilvusManager(
                collection_name=kb.milvus_collection_name,
                embedding_dim=embedding_dim
            )

            logger.info(
                f"Vector search in KB {knowledgebase_id}: "
                f"collection={kb.milvus_collection_name}, model={embedding_model}, dim={embedding_dim}"
            )

            # Generate query embedding
            query_embedding = await embedding_service.embed_text(query)

            # Search in KB's Milvus collection
            results = await milvus_manager.search(
                query_embedding=query_embedding,
                top_k=limit,
                filters=f'knowledgebase_id == "{knowledgebase_id}"'
            )

            # Convert results to standard format
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "type": "document",
                    "document_id": getattr(result, 'document_id', '') or result.get('document_id', '') if isinstance(result, dict) else getattr(result, 'document_id', ''),
                    "chunk_id": getattr(result, 'id', '') or result.get('id', '') if isinstance(result, dict) else getattr(result, 'id', ''),
                    "content": getattr(result, 'text', '') or result.get('text', '') if isinstance(result, dict) else getattr(result, 'text', ''),
                    "score": float(getattr(result, 'score', 0.0) if not isinstance(result, dict) else result.get('score', 0.0)),
                    "metadata": result.get('metadata', {}) if isinstance(result, dict) else {},
                })

            logger.info(f"Vector search returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Vector search error: {str(e)}", exc_info=True)
            return []
    
    async def _knowledge_graph_search(
        self,
        knowledgebase_id: str,
        query: str,
        limit: int,
        include_entities: bool = True,
        include_relationships: bool = True,
    ) -> Dict[str, Any]:
        """Perform knowledge graph search."""
        
        results = {
            "entities": [],
            "relationships": [],
        }
        
        try:
            # Get knowledge graph ID
            kb = self.db.query(Knowledgebase).filter(Knowledgebase.id == knowledgebase_id).first()
            if not kb or not kb.knowledge_graph:
                return results
            
            kg_id = str(kb.knowledge_graph.id)
            
            # Search entities
            if include_entities:
                entities = await self.kg_service.search_entities(
                    kg_id=kg_id,
                    query=query,
                    limit=limit // 2 if include_relationships else limit
                )
                
                results["entities"] = [
                    {
                        "type": "entity",
                        "entity_id": entity["id"],
                        "name": entity["name"],
                        "entity_type": entity["entity_type"],
                        "description": entity.get("description"),
                        "confidence_score": entity["confidence_score"],
                        "mention_count": entity["mention_count"],
                        "relationship_count": entity["relationship_count"],
                        "properties": entity.get("properties", {}),
                    }
                    for entity in entities
                ]
            
            # Search relationships
            if include_relationships:
                relationships = await self.kg_service.find_relationships(
                    kg_id=kg_id,
                    limit=limit // 2 if include_entities else limit
                )
                
                results["relationships"] = [
                    {
                        "type": "relationship",
                        "relationship_id": rel["id"],
                        "relation_type": rel["relation_type"],
                        "relation_label": rel.get("relation_label"),
                        "description": rel.get("description"),
                        "confidence_score": rel["confidence_score"],
                        "source_entity": rel["source_entity"],
                        "target_entity": rel["target_entity"],
                        "is_bidirectional": rel["is_bidirectional"],
                        "properties": rel.get("properties", {}),
                    }
                    for rel in relationships
                ]
            
        except Exception as e:
            logger.error(f"Knowledge graph search error: {str(e)}")
        
        return results
    
    async def _hybrid_search(
        self,
        knowledgebase_id: str,
        query: str,
        limit: int,
        vector_weight: float,
        graph_weight: float,
        include_entities: bool = True,
        include_relationships: bool = True,
        entity_expansion_depth: int = 1,
    ) -> Dict[str, Any]:
        """Perform hybrid search combining vector and graph results."""
        
        # Calculate limits for each search type
        vector_limit = max(1, int(limit * vector_weight))
        graph_limit = max(1, int(limit * graph_weight))
        
        # Perform searches in parallel
        vector_task = self._vector_search(knowledgebase_id, query, vector_limit)
        graph_task = self._knowledge_graph_search(
            knowledgebase_id, query, graph_limit, include_entities, include_relationships
        )
        
        vector_results, graph_results = await asyncio.gather(
            vector_task, graph_task, return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(vector_results, Exception):
            logger.error(f"Vector search failed in hybrid: {str(vector_results)}")
            vector_results = []
        
        if isinstance(graph_results, Exception):
            logger.error(f"Graph search failed in hybrid: {str(graph_results)}")
            graph_results = {"entities": [], "relationships": []}
        
        # Combine and rank results
        combined_results = {
            "documents": vector_results,
            "entities": graph_results.get("entities", []),
            "relationships": graph_results.get("relationships", []),
        }
        
        # Entity expansion: find related entities for high-scoring entities
        if entity_expansion_depth > 0 and combined_results["entities"]:
            try:
                expanded_entities = await self._expand_entities(
                    knowledgebase_id, 
                    combined_results["entities"][:3],  # Expand top 3 entities
                    entity_expansion_depth
                )
                
                # Add expanded entities (avoid duplicates)
                existing_entity_ids = {e["entity_id"] for e in combined_results["entities"]}
                for entity in expanded_entities:
                    if entity["entity_id"] not in existing_entity_ids:
                        combined_results["entities"].append(entity)
                        existing_entity_ids.add(entity["entity_id"])
                
            except Exception as e:
                logger.error(f"Entity expansion failed: {str(e)}")
        
        # Re-rank and limit results
        combined_results["documents"] = combined_results["documents"][:limit]
        combined_results["entities"] = combined_results["entities"][:limit]
        combined_results["relationships"] = combined_results["relationships"][:limit]
        
        return combined_results
    
    async def _expand_entities(
        self,
        knowledgebase_id: str,
        seed_entities: List[Dict[str, Any]],
        depth: int,
    ) -> List[Dict[str, Any]]:
        """Expand entities by finding related entities through relationships."""
        
        if depth <= 0 or not seed_entities:
            return []
        
        try:
            # Get knowledge graph ID
            kb = self.db.query(Knowledgebase).filter(Knowledgebase.id == knowledgebase_id).first()
            if not kb or not kb.knowledge_graph:
                return []
            
            kg_id = str(kb.knowledge_graph.id)
            expanded_entities = []
            
            for seed_entity in seed_entities:
                entity_id = seed_entity["entity_id"]
                
                # Find relationships for this entity
                relationships = await self.kg_service.find_relationships(
                    kg_id=kg_id,
                    entity_id=entity_id,
                    limit=10
                )
                
                # Extract related entities
                for rel in relationships:
                    # Add source entity if it's not the seed
                    if rel["source_entity"]["id"] != entity_id:
                        expanded_entities.append({
                            "type": "entity",
                            "entity_id": rel["source_entity"]["id"],
                            "name": rel["source_entity"]["name"],
                            "entity_type": rel["source_entity"]["entity_type"],
                            "confidence_score": 0.8,  # Lower confidence for expanded
                            "expansion_relation": rel["relation_type"],
                            "expansion_source": seed_entity["name"],
                        })
                    
                    # Add target entity if it's not the seed
                    if rel["target_entity"]["id"] != entity_id:
                        expanded_entities.append({
                            "type": "entity",
                            "entity_id": rel["target_entity"]["id"],
                            "name": rel["target_entity"]["name"],
                            "entity_type": rel["target_entity"]["entity_type"],
                            "confidence_score": 0.8,  # Lower confidence for expanded
                            "expansion_relation": rel["relation_type"],
                            "expansion_source": seed_entity["name"],
                        })
            
            return expanded_entities
            
        except Exception as e:
            logger.error(f"Entity expansion error: {str(e)}")
            return []
    
    async def get_entity_context(
        self,
        knowledgebase_id: str,
        entity_id: str,
        context_depth: int = 2,
    ) -> Dict[str, Any]:
        """Get rich context for an entity including related entities and relationships."""
        
        try:
            # Get knowledge graph ID
            kb = self.db.query(Knowledgebase).filter(Knowledgebase.id == knowledgebase_id).first()
            if not kb or not kb.knowledge_graph:
                return {}
            
            kg_id = str(kb.knowledge_graph.id)
            
            # Get subgraph around the entity
            subgraph = await self.kg_service.get_subgraph(
                kg_id=kg_id,
                entity_ids=[entity_id],
                depth=context_depth
            )
            
            return {
                "entity_id": entity_id,
                "context": subgraph,
                "context_depth": context_depth,
            }
            
        except Exception as e:
            logger.error(f"Error getting entity context: {str(e)}")
            return {}
    
    async def find_entity_paths(
        self,
        knowledgebase_id: str,
        source_entity_id: str,
        target_entity_id: str,
        max_depth: int = 3,
    ) -> List[List[Dict[str, Any]]]:
        """Find paths between two entities in the knowledge graph."""
        
        try:
            # Get knowledge graph ID
            kb = self.db.query(Knowledgebase).filter(Knowledgebase.id == knowledgebase_id).first()
            if not kb or not kb.knowledge_graph:
                return []
            
            kg_id = str(kb.knowledge_graph.id)
            
            # Find paths
            paths = await self.kg_service.find_path(
                kg_id=kg_id,
                source_entity_id=source_entity_id,
                target_entity_id=target_entity_id,
                max_depth=max_depth
            )
            
            return paths
            
        except Exception as e:
            logger.error(f"Error finding entity paths: {str(e)}")
            return []
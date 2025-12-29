"""
Knowledge Graph Service

Handles knowledge graph creation, entity extraction, relationship discovery,
and graph-based search operations.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from backend.db.models.knowledge_graph import (
    KnowledgeGraph,
    KGEntity,
    KGRelationship,
    KGEntityMention,
    KGQuery,
    KGSchema,
    KGExtractionJob,
    EntityType,
    RelationType,
)
from backend.db.models.agent_builder import Knowledgebase, KnowledgebaseDocument
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


class KnowledgeGraphService:
    """Service for managing knowledge graphs."""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Entity extraction models (would be loaded from actual NLP libraries)
        self.entity_extractors = {
            "spacy_en_core_web_sm": self._spacy_entity_extractor,
            "transformers_ner": self._transformers_entity_extractor,
        }
        
        # Relation extraction models
        self.relation_extractors = {
            "rebel_large": self._rebel_relation_extractor,
            "openie": self._openie_relation_extractor,
        }
    
    async def create_knowledge_graph(
        self, 
        knowledgebase_id: str, 
        user_id: str,
        name: str,
        description: str = None,
        auto_extraction_enabled: bool = True,
        entity_extraction_model: str = "spacy_en_core_web_sm",
        relation_extraction_model: str = "rebel_large"
    ) -> KnowledgeGraph:
        """Create a new knowledge graph for a knowledgebase."""
        
        # Verify knowledgebase exists and belongs to user
        kb = self.db.query(Knowledgebase).filter(
            Knowledgebase.id == knowledgebase_id,
            Knowledgebase.user_id == user_id
        ).first()
        
        if not kb:
            raise ValueError("Knowledgebase not found or access denied")
        
        # Check if knowledge graph already exists
        existing_kg = self.db.query(KnowledgeGraph).filter(
            KnowledgeGraph.knowledgebase_id == knowledgebase_id
        ).first()
        
        if existing_kg:
            raise ValueError("Knowledge graph already exists for this knowledgebase")
        
        # Create knowledge graph
        kg = KnowledgeGraph(
            knowledgebase_id=knowledgebase_id,
            user_id=user_id,
            name=name,
            description=description,
            auto_extraction_enabled=auto_extraction_enabled,
            entity_extraction_model=entity_extraction_model,
            relation_extraction_model=relation_extraction_model,
        )
        
        self.db.add(kg)
        self.db.flush()
        
        # Update knowledgebase to enable KG
        kb.kg_enabled = True
        
        # If auto extraction is enabled, start extraction job
        if auto_extraction_enabled:
            await self._start_extraction_job(kg.id, user_id, "full_extraction")
        
        self.db.commit()
        
        logger.info(f"Created knowledge graph {kg.id} for knowledgebase {knowledgebase_id}")
        return kg
    
    async def extract_entities_and_relationships(
        self, 
        kg_id: str, 
        document_texts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract entities and relationships from document texts."""
        
        kg = self.db.query(KnowledgeGraph).filter(KnowledgeGraph.id == kg_id).first()
        if not kg:
            raise ValueError("Knowledge graph not found")
        
        extraction_stats = {
            "entities_extracted": 0,
            "relationships_extracted": 0,
            "documents_processed": 0,
            "errors": []
        }
        
        try:
            for doc_data in document_texts:
                try:
                    doc_id = doc_data.get("document_id")
                    text = doc_data.get("text", "")
                    chunks = doc_data.get("chunks", [])
                    
                    if not text:
                        continue
                    
                    # Extract entities
                    entities = await self._extract_entities(
                        text, kg.entity_extraction_model, doc_id, chunks
                    )
                    
                    # Store entities in database
                    entity_map = {}
                    for entity_data in entities:
                        entity = await self._store_entity(kg.id, entity_data)
                        entity_map[entity_data["name"]] = entity
                        extraction_stats["entities_extracted"] += 1
                    
                    # Extract relationships
                    relationships = await self._extract_relationships(
                        text, kg.relation_extraction_model, entity_map, doc_id, chunks
                    )
                    
                    # Store relationships in database
                    for rel_data in relationships:
                        await self._store_relationship(kg.id, rel_data, entity_map)
                        extraction_stats["relationships_extracted"] += 1
                    
                    extraction_stats["documents_processed"] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing document {doc_data.get('document_id', 'unknown')}: {str(e)}"
                    extraction_stats["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # Update knowledge graph statistics
            kg.entity_count = self.db.query(KGEntity).filter(
                KGEntity.knowledge_graph_id == kg_id
            ).count()
            
            kg.relationship_count = self.db.query(KGRelationship).filter(
                KGRelationship.knowledge_graph_id == kg_id
            ).count()
            
            kg.last_processed_at = datetime.utcnow()
            kg.processing_status = "ready"
            
            self.db.commit()
            
        except Exception as e:
            kg.processing_status = "error"
            kg.processing_error = str(e)
            self.db.commit()
            raise
        
        return extraction_stats
    
    async def search_entities(
        self, 
        kg_id: str, 
        query: str, 
        entity_types: List[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search for entities in the knowledge graph."""
        
        # Build query
        db_query = self.db.query(KGEntity).filter(
            KGEntity.knowledge_graph_id == kg_id
        )
        
        # Add text search
        if query:
            search_filter = or_(
                KGEntity.name.ilike(f"%{query}%"),
                KGEntity.canonical_name.ilike(f"%{query}%"),
                KGEntity.description.ilike(f"%{query}%")
            )
            db_query = db_query.filter(search_filter)
        
        # Add entity type filter
        if entity_types:
            db_query = db_query.filter(KGEntity.entity_type.in_(entity_types))
        
        # Order by confidence and limit
        entities = db_query.order_by(
            KGEntity.confidence_score.desc(),
            KGEntity.mention_count.desc()
        ).limit(limit).all()
        
        # Convert to response format
        results = []
        for entity in entities:
            results.append({
                "id": str(entity.id),
                "name": entity.name,
                "canonical_name": entity.canonical_name,
                "entity_type": entity.entity_type,
                "description": entity.description,
                "confidence_score": entity.confidence_score,
                "mention_count": entity.mention_count,
                "relationship_count": entity.relationship_count,
                "properties": entity.properties,
                "aliases": entity.aliases,
            })
        
        # Log query for analytics
        await self._log_query(kg_id, query, "entity_search", len(results))
        
        return results
    
    async def find_relationships(
        self, 
        kg_id: str, 
        entity_id: str = None,
        relation_types: List[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Find relationships in the knowledge graph."""
        
        # Build query
        db_query = self.db.query(KGRelationship).filter(
            KGRelationship.knowledge_graph_id == kg_id
        )
        
        # Add entity filter
        if entity_id:
            db_query = db_query.filter(
                or_(
                    KGRelationship.source_entity_id == entity_id,
                    KGRelationship.target_entity_id == entity_id
                )
            )
        
        # Add relation type filter
        if relation_types:
            db_query = db_query.filter(KGRelationship.relation_type.in_(relation_types))
        
        # Order by confidence and limit
        relationships = db_query.order_by(
            KGRelationship.confidence_score.desc(),
            KGRelationship.mention_count.desc()
        ).limit(limit).all()
        
        # Convert to response format with entity details
        results = []
        for rel in relationships:
            results.append({
                "id": str(rel.id),
                "relation_type": rel.relation_type,
                "relation_label": rel.relation_label,
                "description": rel.description,
                "confidence_score": rel.confidence_score,
                "mention_count": rel.mention_count,
                "is_bidirectional": rel.is_bidirectional,
                "properties": rel.properties,
                "source_entity": {
                    "id": str(rel.source_entity.id),
                    "name": rel.source_entity.name,
                    "entity_type": rel.source_entity.entity_type,
                },
                "target_entity": {
                    "id": str(rel.target_entity.id),
                    "name": rel.target_entity.name,
                    "entity_type": rel.target_entity.entity_type,
                },
                "temporal_start": rel.temporal_start.isoformat() if rel.temporal_start else None,
                "temporal_end": rel.temporal_end.isoformat() if rel.temporal_end else None,
            })
        
        # Log query for analytics
        await self._log_query(kg_id, f"entity:{entity_id}", "relationship_search", len(results))
        
        return results
    
    async def find_path(
        self, 
        kg_id: str, 
        source_entity_id: str, 
        target_entity_id: str,
        max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """Find paths between two entities in the knowledge graph."""
        
        # This is a simplified path finding algorithm
        # In production, you might want to use a graph database like Neo4j
        
        visited = set()
        paths = []
        
        async def dfs(current_id: str, target_id: str, path: List[str], depth: int):
            if depth > max_depth or current_id in visited:
                return
            
            if current_id == target_id:
                paths.append(path.copy())
                return
            
            visited.add(current_id)
            
            # Find all relationships from current entity
            relationships = self.db.query(KGRelationship).filter(
                KGRelationship.knowledge_graph_id == kg_id,
                or_(
                    KGRelationship.source_entity_id == current_id,
                    and_(
                        KGRelationship.target_entity_id == current_id,
                        KGRelationship.is_bidirectional == True
                    )
                )
            ).all()
            
            for rel in relationships:
                next_entity_id = (
                    rel.target_entity_id if rel.source_entity_id == current_id 
                    else rel.source_entity_id
                )
                
                if next_entity_id not in visited:
                    path.append({
                        "relationship_id": str(rel.id),
                        "relation_type": rel.relation_type,
                        "entity_id": next_entity_id
                    })
                    
                    await dfs(next_entity_id, target_id, path, depth + 1)
                    path.pop()
            
            visited.remove(current_id)
        
        await dfs(source_entity_id, target_entity_id, [], 0)
        
        # Log query for analytics
        await self._log_query(
            kg_id, 
            f"path:{source_entity_id}->{target_entity_id}", 
            "path_finding", 
            len(paths)
        )
        
        return paths[:10]  # Return top 10 paths
    
    async def get_subgraph(
        self, 
        kg_id: str, 
        entity_ids: List[str], 
        depth: int = 1
    ) -> Dict[str, Any]:
        """Get a subgraph around specified entities."""
        
        all_entity_ids = set(entity_ids)
        
        # Expand to include connected entities up to specified depth
        for _ in range(depth):
            # Find relationships involving current entities
            relationships = self.db.query(KGRelationship).filter(
                KGRelationship.knowledge_graph_id == kg_id,
                or_(
                    KGRelationship.source_entity_id.in_(all_entity_ids),
                    KGRelationship.target_entity_id.in_(all_entity_ids)
                )
            ).all()
            
            # Add connected entities
            for rel in relationships:
                all_entity_ids.add(rel.source_entity_id)
                all_entity_ids.add(rel.target_entity_id)
        
        # Get all entities in subgraph
        entities = self.db.query(KGEntity).filter(
            KGEntity.id.in_(all_entity_ids)
        ).all()
        
        # Get all relationships in subgraph
        relationships = self.db.query(KGRelationship).filter(
            KGRelationship.knowledge_graph_id == kg_id,
            KGRelationship.source_entity_id.in_(all_entity_ids),
            KGRelationship.target_entity_id.in_(all_entity_ids)
        ).all()
        
        # Format response
        subgraph = {
            "entities": [
                {
                    "id": str(entity.id),
                    "name": entity.name,
                    "entity_type": entity.entity_type,
                    "description": entity.description,
                    "confidence_score": entity.confidence_score,
                    "properties": entity.properties,
                }
                for entity in entities
            ],
            "relationships": [
                {
                    "id": str(rel.id),
                    "source_entity_id": str(rel.source_entity_id),
                    "target_entity_id": str(rel.target_entity_id),
                    "relation_type": rel.relation_type,
                    "relation_label": rel.relation_label,
                    "confidence_score": rel.confidence_score,
                    "is_bidirectional": rel.is_bidirectional,
                    "properties": rel.properties,
                }
                for rel in relationships
            ]
        }
        
        # Log query for analytics
        await self._log_query(
            kg_id, 
            f"subgraph:{','.join(entity_ids)}", 
            "subgraph", 
            len(entities)
        )
        
        return subgraph
    
    # Private helper methods
    
    async def _extract_entities(
        self, 
        text: str, 
        model_name: str, 
        doc_id: str = None, 
        chunks: List[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Extract entities from text using specified model."""
        
        extractor = self.entity_extractors.get(model_name, self._spacy_entity_extractor)
        return await extractor(text, doc_id, chunks)
    
    async def _extract_relationships(
        self, 
        text: str, 
        model_name: str, 
        entity_map: Dict[str, KGEntity],
        doc_id: str = None, 
        chunks: List[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Extract relationships from text using specified model."""
        
        extractor = self.relation_extractors.get(model_name, self._rebel_relation_extractor)
        return await extractor(text, entity_map, doc_id, chunks)
    
    async def _spacy_entity_extractor(
        self, 
        text: str, 
        doc_id: str = None, 
        chunks: List[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Extract entities using spaCy (mock implementation)."""
        
        # This is a mock implementation
        # In production, you would use actual spaCy models
        
        entities = []
        
        # Simple regex-based entity extraction for demo
        patterns = {
            EntityType.PERSON: r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            EntityType.ORGANIZATION: r'\b[A-Z][a-z]+ (?:Inc|Corp|LLC|Ltd|Company|Organization)\b',
            EntityType.LOCATION: r'\b(?:New York|California|London|Paris|Tokyo|Seoul)\b',
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entity_name = match.group()
                entities.append({
                    "name": entity_name,
                    "canonical_name": entity_name.lower().strip(),
                    "entity_type": entity_type.value,
                    "confidence_score": 0.8,
                    "start_position": match.start(),
                    "end_position": match.end(),
                    "source_documents": [doc_id] if doc_id else [],
                    "extraction_source": "auto",
                })
        
        return entities
    
    async def _transformers_entity_extractor(
        self, 
        text: str, 
        doc_id: str = None, 
        chunks: List[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Extract entities using Transformers NER model (mock implementation)."""
        
        # Mock implementation - would use actual transformers model
        return await self._spacy_entity_extractor(text, doc_id, chunks)
    
    async def _rebel_relation_extractor(
        self, 
        text: str, 
        entity_map: Dict[str, KGEntity],
        doc_id: str = None, 
        chunks: List[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Extract relationships using REBEL model (mock implementation)."""
        
        relationships = []
        
        # Simple pattern-based relationship extraction for demo
        entity_names = list(entity_map.keys())
        
        for i, entity1 in enumerate(entity_names):
            for entity2 in entity_names[i+1:]:
                # Look for entities mentioned together
                if entity1 in text and entity2 in text:
                    # Simple heuristics for relationship types
                    if "works for" in text or "employee of" in text:
                        rel_type = RelationType.WORKS_FOR
                    elif "located in" in text or "based in" in text:
                        rel_type = RelationType.LOCATED_IN
                    elif "part of" in text or "division of" in text:
                        rel_type = RelationType.PART_OF
                    else:
                        rel_type = RelationType.RELATED_TO
                    
                    relationships.append({
                        "source_entity_name": entity1,
                        "target_entity_name": entity2,
                        "relation_type": rel_type.value,
                        "confidence_score": 0.7,
                        "source_documents": [doc_id] if doc_id else [],
                        "extraction_source": "auto",
                    })
        
        return relationships
    
    async def _openie_relation_extractor(
        self, 
        text: str, 
        entity_map: Dict[str, KGEntity],
        doc_id: str = None, 
        chunks: List[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Extract relationships using OpenIE (mock implementation)."""
        
        # Mock implementation - would use actual OpenIE system
        return await self._rebel_relation_extractor(text, entity_map, doc_id, chunks)
    
    async def _store_entity(self, kg_id: str, entity_data: Dict[str, Any]) -> KGEntity:
        """Store or update entity in database."""
        
        canonical_name = entity_data["canonical_name"]
        
        # Check if entity already exists
        existing_entity = self.db.query(KGEntity).filter(
            KGEntity.knowledge_graph_id == kg_id,
            KGEntity.canonical_name == canonical_name
        ).first()
        
        if existing_entity:
            # Update existing entity
            existing_entity.mention_count += 1
            existing_entity.confidence_score = max(
                existing_entity.confidence_score, 
                entity_data.get("confidence_score", 0.5)
            )
            
            # Merge source documents
            if entity_data.get("source_documents"):
                existing_docs = set(existing_entity.source_documents or [])
                new_docs = set(entity_data["source_documents"])
                existing_entity.source_documents = list(existing_docs | new_docs)
            
            return existing_entity
        else:
            # Create new entity
            entity = KGEntity(
                knowledge_graph_id=kg_id,
                name=entity_data["name"],
                canonical_name=canonical_name,
                entity_type=entity_data["entity_type"],
                description=entity_data.get("description"),
                confidence_score=entity_data.get("confidence_score", 0.5),
                extraction_source=entity_data.get("extraction_source", "auto"),
                source_documents=entity_data.get("source_documents", []),
                properties=entity_data.get("properties", {}),
                aliases=entity_data.get("aliases", []),
            )
            
            self.db.add(entity)
            self.db.flush()
            return entity
    
    async def _store_relationship(
        self, 
        kg_id: str, 
        rel_data: Dict[str, Any], 
        entity_map: Dict[str, KGEntity]
    ) -> KGRelationship:
        """Store or update relationship in database."""
        
        source_entity = entity_map.get(rel_data["source_entity_name"])
        target_entity = entity_map.get(rel_data["target_entity_name"])
        
        if not source_entity or not target_entity:
            return None
        
        # Check if relationship already exists
        existing_rel = self.db.query(KGRelationship).filter(
            KGRelationship.knowledge_graph_id == kg_id,
            KGRelationship.source_entity_id == source_entity.id,
            KGRelationship.target_entity_id == target_entity.id,
            KGRelationship.relation_type == rel_data["relation_type"]
        ).first()
        
        if existing_rel:
            # Update existing relationship
            existing_rel.mention_count += 1
            existing_rel.confidence_score = max(
                existing_rel.confidence_score,
                rel_data.get("confidence_score", 0.5)
            )
            return existing_rel
        else:
            # Create new relationship
            relationship = KGRelationship(
                knowledge_graph_id=kg_id,
                source_entity_id=source_entity.id,
                target_entity_id=target_entity.id,
                relation_type=rel_data["relation_type"],
                relation_label=rel_data.get("relation_label"),
                description=rel_data.get("description"),
                confidence_score=rel_data.get("confidence_score", 0.5),
                extraction_source=rel_data.get("extraction_source", "auto"),
                source_documents=rel_data.get("source_documents", []),
                properties=rel_data.get("properties", {}),
            )
            
            self.db.add(relationship)
            self.db.flush()
            
            # Update entity relationship counts
            source_entity.relationship_count += 1
            target_entity.relationship_count += 1
            
            return relationship
    
    async def _start_extraction_job(
        self, 
        kg_id: str, 
        user_id: str, 
        job_type: str
    ) -> KGExtractionJob:
        """Start a knowledge graph extraction job."""
        
        job = KGExtractionJob(
            knowledge_graph_id=kg_id,
            user_id=user_id,
            job_type=job_type,
            status="pending",
        )
        
        self.db.add(job)
        self.db.flush()
        
        # In production, this would trigger an async background task
        logger.info(f"Started KG extraction job {job.id} for graph {kg_id}")
        
        return job
    
    async def _log_query(
        self, 
        kg_id: str, 
        query_text: str, 
        query_type: str, 
        result_count: int
    ):
        """Log query for analytics."""
        
        # Get user_id from knowledge graph
        kg = self.db.query(KnowledgeGraph).filter(KnowledgeGraph.id == kg_id).first()
        if not kg:
            return
        
        query_log = KGQuery(
            knowledge_graph_id=kg_id,
            user_id=kg.user_id,
            query_text=query_text,
            query_type=query_type,
            result_count=result_count,
        )
        
        self.db.add(query_log)
        # Don't commit here - let the calling method handle it
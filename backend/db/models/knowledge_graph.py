"""
Knowledge Graph models for structured knowledge representation.

Implements graph-based knowledge storage with entities, relationships,
and semantic search capabilities.
"""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    Text,
    Float,
    ForeignKey,
    Index,
    CheckConstraint,
    UniqueConstraint,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.db.database import Base


class EntityType(str, enum.Enum):
    """Entity types in the knowledge graph."""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    CONCEPT = "concept"
    EVENT = "event"
    PRODUCT = "product"
    DOCUMENT = "document"
    TOPIC = "topic"
    CUSTOM = "custom"


class RelationType(str, enum.Enum):
    """Relationship types between entities."""
    # Hierarchical relationships
    IS_A = "is_a"
    PART_OF = "part_of"
    BELONGS_TO = "belongs_to"
    
    # Associative relationships
    RELATED_TO = "related_to"
    SIMILAR_TO = "similar_to"
    OPPOSITE_TO = "opposite_to"
    
    # Temporal relationships
    BEFORE = "before"
    AFTER = "after"
    DURING = "during"
    
    # Causal relationships
    CAUSES = "causes"
    ENABLES = "enables"
    PREVENTS = "prevents"
    
    # Social relationships
    WORKS_FOR = "works_for"
    COLLABORATES_WITH = "collaborates_with"
    COMPETES_WITH = "competes_with"
    
    # Spatial relationships
    LOCATED_IN = "located_in"
    NEAR = "near"
    
    # Custom relationships
    CUSTOM = "custom"


# ============================================================================
# KNOWLEDGE GRAPH MODELS
# ============================================================================


class KnowledgeGraph(Base):
    """Knowledge Graph container for a knowledgebase."""

    __tablename__ = "knowledge_graphs"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    knowledgebase_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledgebases.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Graph Configuration
    auto_extraction_enabled = Column(Boolean, default=True)
    entity_extraction_model = Column(String(100), default="spacy_en_core_web_sm")
    relation_extraction_model = Column(String(100), default="rebel_large")
    
    # Graph Statistics
    entity_count = Column(Integer, default=0)
    relationship_count = Column(Integer, default=0)
    
    # Processing Status
    last_processed_at = Column(DateTime)
    processing_status = Column(String(50), default="ready")  # ready, processing, error
    processing_error = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    entities = relationship("KGEntity", back_populates="knowledge_graph", cascade="all, delete-orphan")
    relationships = relationship("KGRelationship", back_populates="knowledge_graph", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_kg_user_created", "user_id", "created_at"),
        CheckConstraint(
            "processing_status IN ('ready', 'processing', 'error', 'updating')",
            name="check_kg_processing_status_valid",
        ),
    )

    def __repr__(self):
        return f"<KnowledgeGraph(id={self.id}, name={self.name})>"


class KGEntity(Base):
    """Entity in the knowledge graph."""

    __tablename__ = "kg_entities"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    knowledge_graph_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Entity Information
    name = Column(String(500), nullable=False)
    entity_type = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    
    # Canonical form for deduplication
    canonical_name = Column(String(500), nullable=False, index=True)
    
    # Entity Properties
    properties = Column(JSONB, default=dict)
    aliases = Column(JSONB, default=list)  # Alternative names
    
    # Confidence and Quality Metrics
    confidence_score = Column(Float, default=1.0)
    extraction_source = Column(String(100))  # auto, manual, imported
    
    # Vector Embedding for semantic search
    embedding = Column(JSONB)  # Store as JSON array
    
    # Source Information
    source_documents = Column(JSONB, default=list)  # Document IDs where entity was found
    source_chunks = Column(JSONB, default=list)  # Specific chunk references
    
    # Statistics
    mention_count = Column(Integer, default=1)
    relationship_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    knowledge_graph = relationship("KnowledgeGraph", back_populates="entities")
    source_relationships = relationship(
        "KGRelationship",
        foreign_keys="KGRelationship.source_entity_id",
        back_populates="source_entity",
        cascade="all, delete-orphan"
    )
    target_relationships = relationship(
        "KGRelationship",
        foreign_keys="KGRelationship.target_entity_id",
        back_populates="target_entity",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_kg_entities_kg_type", "knowledge_graph_id", "entity_type"),
        Index("ix_kg_entities_canonical", "canonical_name"),
        Index("ix_kg_entities_confidence", "confidence_score"),
        UniqueConstraint("knowledge_graph_id", "canonical_name", name="uq_kg_entity_canonical"),
        CheckConstraint("confidence_score >= 0.0 AND confidence_score <= 1.0", name="check_entity_confidence_range"),
        CheckConstraint("mention_count >= 0", name="check_entity_mention_count_positive"),
    )

    def __repr__(self):
        return f"<KGEntity(id={self.id}, name={self.name}, type={self.entity_type})>"


class KGRelationship(Base):
    """Relationship between entities in the knowledge graph."""

    __tablename__ = "kg_relationships"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    knowledge_graph_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_entity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("kg_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_entity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("kg_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationship Information
    relation_type = Column(String(50), nullable=False, index=True)
    relation_label = Column(String(200))  # Human-readable label
    description = Column(Text)
    
    # Relationship Properties
    properties = Column(JSONB, default=dict)
    
    # Directionality
    is_bidirectional = Column(Boolean, default=False)
    
    # Confidence and Quality Metrics
    confidence_score = Column(Float, default=1.0)
    extraction_source = Column(String(100))  # auto, manual, imported
    
    # Source Information
    source_documents = Column(JSONB, default=list)
    source_chunks = Column(JSONB, default=list)
    source_sentences = Column(JSONB, default=list)  # Specific sentences where relation was found
    
    # Temporal Information
    temporal_start = Column(DateTime)
    temporal_end = Column(DateTime)
    
    # Statistics
    mention_count = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    knowledge_graph = relationship("KnowledgeGraph", back_populates="relationships")
    source_entity = relationship(
        "KGEntity",
        foreign_keys=[source_entity_id],
        back_populates="source_relationships"
    )
    target_entity = relationship(
        "KGEntity",
        foreign_keys=[target_entity_id],
        back_populates="target_relationships"
    )

    __table_args__ = (
        Index("ix_kg_relationships_kg_type", "knowledge_graph_id", "relation_type"),
        Index("ix_kg_relationships_source_target", "source_entity_id", "target_entity_id"),
        Index("ix_kg_relationships_confidence", "confidence_score"),
        Index("ix_kg_relationships_temporal", "temporal_start", "temporal_end"),
        UniqueConstraint(
            "knowledge_graph_id", "source_entity_id", "target_entity_id", "relation_type",
            name="uq_kg_relationship"
        ),
        CheckConstraint("confidence_score >= 0.0 AND confidence_score <= 1.0", name="check_relationship_confidence_range"),
        CheckConstraint("mention_count >= 0", name="check_relationship_mention_count_positive"),
        CheckConstraint("source_entity_id != target_entity_id", name="check_no_self_relationship"),
    )

    def __repr__(self):
        return f"<KGRelationship(id={self.id}, type={self.relation_type})>"


class KGEntityMention(Base):
    """Specific mentions of entities in documents."""

    __tablename__ = "kg_entity_mentions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    entity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("kg_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Mention Information
    mention_text = Column(Text, nullable=False)
    context_before = Column(Text)
    context_after = Column(Text)
    
    # Position Information
    chunk_id = Column(String(100))
    start_position = Column(Integer)
    end_position = Column(Integer)
    
    # Confidence
    confidence_score = Column(Float, default=1.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_kg_mentions_entity_doc", "entity_id", "document_id"),
        Index("ix_kg_mentions_confidence", "confidence_score"),
        CheckConstraint("confidence_score >= 0.0 AND confidence_score <= 1.0", name="check_mention_confidence_range"),
    )

    def __repr__(self):
        return f"<KGEntityMention(id={self.id}, text={self.mention_text[:50]})>"


class KGQuery(Base):
    """Stored knowledge graph queries for analytics and optimization."""

    __tablename__ = "kg_queries"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    knowledge_graph_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Query Information
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), nullable=False)  # entity_search, path_finding, subgraph, etc.
    query_parameters = Column(JSONB, default=dict)
    
    # Results
    result_count = Column(Integer, default=0)
    execution_time_ms = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_kg_queries_kg_user", "knowledge_graph_id", "user_id"),
        Index("ix_kg_queries_type_created", "query_type", "created_at"),
        CheckConstraint(
            "query_type IN ('entity_search', 'relationship_search', 'path_finding', 'subgraph', 'similarity', 'custom')",
            name="check_kg_query_type_valid",
        ),
    )

    def __repr__(self):
        return f"<KGQuery(id={self.id}, type={self.query_type})>"


# ============================================================================
# KNOWLEDGE GRAPH SCHEMA MODELS
# ============================================================================


class KGSchema(Base):
    """Schema definition for knowledge graph structure."""

    __tablename__ = "kg_schemas"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    knowledge_graph_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Schema Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Schema Definition
    entity_types = Column(JSONB, nullable=False, default=list)
    relationship_types = Column(JSONB, nullable=False, default=list)
    constraints = Column(JSONB, default=dict)
    
    # Validation Rules
    validation_rules = Column(JSONB, default=dict)
    
    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("knowledge_graph_id", "name", name="uq_kg_schema_name"),
    )

    def __repr__(self):
        return f"<KGSchema(id={self.id}, name={self.name})>"


class KGExtractionJob(Base):
    """Knowledge graph extraction job tracking."""

    __tablename__ = "kg_extraction_jobs"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    knowledge_graph_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Job Information
    job_type = Column(String(50), nullable=False)  # full_extraction, incremental, document_specific
    status = Column(String(50), nullable=False, default="pending")
    
    # Processing Details
    documents_to_process = Column(JSONB, default=list)
    documents_processed = Column(Integer, default=0)
    documents_total = Column(Integer, default=0)
    
    # Results
    entities_extracted = Column(Integer, default=0)
    relationships_extracted = Column(Integer, default=0)
    
    # Error Handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    estimated_completion = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_kg_jobs_kg_status", "knowledge_graph_id", "status"),
        Index("ix_kg_jobs_user_created", "user_id", "created_at"),
        CheckConstraint(
            "job_type IN ('full_extraction', 'incremental', 'document_specific', 'schema_update')",
            name="check_kg_job_type_valid",
        ),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'cancelled')",
            name="check_kg_job_status_valid",
        ),
    )

    def __repr__(self):
        return f"<KGExtractionJob(id={self.id}, type={self.job_type}, status={self.status})>"
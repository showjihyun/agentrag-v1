"""
Eager Loading Utilities for N+1 Query Prevention.

Provides utilities and patterns for efficient relationship loading
to prevent N+1 query problems.
"""

from typing import List, Type, TypeVar, Optional, Dict, Any
from sqlalchemy.orm import Session, Query, selectinload, joinedload, subqueryload
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class EagerLoadingMixin:
    """
    Mixin class providing eager loading utilities for repositories.
    
    Usage:
        class UserRepository(EagerLoadingMixin):
            def __init__(self, db: Session):
                self.db = db
                self.model = User
            
            def get_with_documents(self, user_id: UUID) -> Optional[User]:
                return self.get_with_relations(
                    user_id,
                    relations=['documents', 'sessions']
                )
    """
    
    db: Session
    model: Type[T]
    
    def get_with_relations(
        self,
        entity_id: Any,
        relations: List[str],
        strategy: str = "selectin"
    ) -> Optional[T]:
        """
        Get entity by ID with eager-loaded relations.
        
        Args:
            entity_id: Entity primary key
            relations: List of relationship names to load
            strategy: Loading strategy ('selectin', 'joined', 'subquery')
        
        Returns:
            Entity with loaded relations or None
        
        Example:
            user = repo.get_with_relations(
                user_id,
                relations=['documents', 'sessions'],
                strategy='selectin'
            )
        """
        query = self.db.query(self.model).filter(self.model.id == entity_id)
        query = self._apply_eager_loading(query, relations, strategy)
        return query.first()
    
    def get_all_with_relations(
        self,
        relations: List[str],
        filters: Dict[str, Any] = None,
        limit: int = 100,
        offset: int = 0,
        strategy: str = "selectin"
    ) -> List[T]:
        """
        Get all entities with eager-loaded relations.
        
        Args:
            relations: List of relationship names to load
            filters: Optional filter conditions
            limit: Maximum results
            offset: Offset for pagination
            strategy: Loading strategy
        
        Returns:
            List of entities with loaded relations
        """
        query = self.db.query(self.model)
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        # Apply eager loading
        query = self._apply_eager_loading(query, relations, strategy)
        
        return query.limit(limit).offset(offset).all()
    
    def _apply_eager_loading(
        self,
        query: Query,
        relations: List[str],
        strategy: str = "selectin"
    ) -> Query:
        """
        Apply eager loading options to query.
        
        Strategies:
        - selectin: Uses SELECT IN for loading (best for collections)
        - joined: Uses JOIN (best for single relations)
        - subquery: Uses subquery (good for complex relations)
        """
        loader_map = {
            "selectin": selectinload,
            "joined": joinedload,
            "subquery": subqueryload,
        }
        
        loader = loader_map.get(strategy, selectinload)
        
        for relation in relations:
            if hasattr(self.model, relation):
                query = query.options(loader(getattr(self.model, relation)))
            else:
                logger.warning(
                    f"Relation '{relation}' not found on model {self.model.__name__}"
                )
        
        return query


def with_eager_loading(
    query: Query,
    relations: List[str],
    model: Type[T],
    strategy: str = "selectin"
) -> Query:
    """
    Standalone function to apply eager loading to any query.
    
    Args:
        query: SQLAlchemy query
        relations: List of relationship names
        model: Model class
        strategy: Loading strategy
    
    Returns:
        Query with eager loading options
    
    Example:
        query = db.query(User).filter(User.is_active == True)
        query = with_eager_loading(query, ['documents', 'sessions'], User)
        users = query.all()
    """
    loader_map = {
        "selectin": selectinload,
        "joined": joinedload,
        "subquery": subqueryload,
    }
    
    loader = loader_map.get(strategy, selectinload)
    
    for relation in relations:
        if hasattr(model, relation):
            query = query.options(loader(getattr(model, relation)))
    
    return query


# ============================================================================
# Common Eager Loading Patterns
# ============================================================================

class UserEagerLoader:
    """
    Pre-defined eager loading patterns for User model.
    
    Usage:
        users = UserEagerLoader.with_documents(db).filter(...).all()
    """
    
    @staticmethod
    def with_documents(db: Session) -> Query:
        """Load user with documents."""
        from backend.db.models.user import User
        return db.query(User).options(selectinload(User.documents))
    
    @staticmethod
    def with_sessions(db: Session) -> Query:
        """Load user with sessions."""
        from backend.db.models.user import User
        return db.query(User).options(selectinload(User.sessions))
    
    @staticmethod
    def with_all_relations(db: Session) -> Query:
        """Load user with all common relations."""
        from backend.db.models.user import User
        return db.query(User).options(
            selectinload(User.documents),
            selectinload(User.sessions),
            selectinload(User.bookmarks),
        )
    
    @staticmethod
    def for_profile(db: Session) -> Query:
        """Load user data needed for profile display."""
        from backend.db.models.user import User
        return db.query(User).options(
            selectinload(User.documents),
            selectinload(User.usage_logs),
        )


class WorkflowEagerLoader:
    """
    Pre-defined eager loading patterns for Workflow model.
    """
    
    @staticmethod
    def with_nodes(db: Session) -> Query:
        """Load workflow with nodes."""
        from backend.db.models.agent_builder import Workflow
        return db.query(Workflow).options(selectinload(Workflow.nodes))
    
    @staticmethod
    def with_executions(db: Session) -> Query:
        """Load workflow with recent executions."""
        from backend.db.models.agent_builder import Workflow
        return db.query(Workflow).options(selectinload(Workflow.executions))
    
    @staticmethod
    def with_all(db: Session) -> Query:
        """Load workflow with all relations."""
        from backend.db.models.agent_builder import Workflow
        return db.query(Workflow).options(
            selectinload(Workflow.nodes),
            selectinload(Workflow.executions),
            selectinload(Workflow.variables),
        )


# ============================================================================
# Batch Loading Utilities
# ============================================================================

async def batch_load_relations(
    db: Session,
    entities: List[T],
    relation: str,
    batch_size: int = 100
) -> None:
    """
    Batch load a relation for multiple entities.
    
    Useful when you already have entities and need to load relations
    without N+1 queries.
    
    Args:
        db: Database session
        entities: List of entities
        relation: Relation name to load
        batch_size: Batch size for loading
    
    Example:
        users = db.query(User).limit(100).all()
        await batch_load_relations(db, users, 'documents')
        # Now users[0].documents is loaded without N+1
    """
    if not entities:
        return
    
    model = type(entities[0])
    
    if not hasattr(model, relation):
        logger.warning(f"Relation '{relation}' not found on {model.__name__}")
        return
    
    # Get entity IDs
    entity_ids = [e.id for e in entities]
    
    # Load in batches
    for i in range(0, len(entity_ids), batch_size):
        batch_ids = entity_ids[i:i + batch_size]
        
        # Query with eager loading
        loaded = db.query(model).filter(
            model.id.in_(batch_ids)
        ).options(
            selectinload(getattr(model, relation))
        ).all()
        
        # Map loaded entities back
        loaded_map = {e.id: e for e in loaded}
        
        for entity in entities:
            if entity.id in loaded_map:
                # Copy loaded relation to original entity
                loaded_entity = loaded_map[entity.id]
                setattr(entity, relation, getattr(loaded_entity, relation))


def prefetch_related(
    db: Session,
    model: Type[T],
    ids: List[Any],
    relations: List[str]
) -> Dict[Any, T]:
    """
    Prefetch entities with relations by IDs.
    
    Returns a dictionary mapping ID to entity for easy lookup.
    
    Args:
        db: Database session
        model: Model class
        ids: List of entity IDs
        relations: Relations to load
    
    Returns:
        Dict mapping ID to entity
    
    Example:
        user_map = prefetch_related(db, User, user_ids, ['documents'])
        for user_id in user_ids:
            user = user_map.get(user_id)
            if user:
                print(user.documents)  # Already loaded
    """
    if not ids:
        return {}
    
    query = db.query(model).filter(model.id.in_(ids))
    
    for relation in relations:
        if hasattr(model, relation):
            query = query.options(selectinload(getattr(model, relation)))
    
    entities = query.all()
    
    return {e.id: e for e in entities}

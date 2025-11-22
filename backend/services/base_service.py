"""
Base service class with common functionality.
"""
from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from backend.exceptions import ResourceNotFoundError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseService(Generic[T]):
    """
    Base service class with common CRUD operations.
    
    Provides standard methods for database operations with
    error handling and logging.
    """
    
    def __init__(self, db: Session, model: Type[T]):
        """
        Initialize base service.
        
        Args:
            db: Database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model
        self.model_name = model.__name__
    
    def get_by_id(
        self,
        id: Any,
        raise_if_not_found: bool = True
    ) -> Optional[T]:
        """
        Get entity by ID.
        
        Args:
            id: Entity ID
            raise_if_not_found: Raise exception if not found
            
        Returns:
            Entity or None
            
        Raises:
            ResourceNotFoundError: If entity not found and raise_if_not_found=True
        """
        try:
            entity = self.db.query(self.model).filter(
                self.model.id == id
            ).first()
            
            if not entity and raise_if_not_found:
                raise ResourceNotFoundError(
                    resource_type=self.model_name,
                    resource_id=str(id)
                )
            
            return entity
            
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting {self.model_name}",
                extra={"id": id, "error": str(e)}
            )
            raise
    
    def get_by_user(
        self,
        user_id: Any,
        limit: int = 100,
        offset: int = 0
    ) -> List[T]:
        """
        Get entities by user ID.
        
        Args:
            user_id: User ID
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            List of entities
        """
        try:
            return self.db.query(self.model).filter(
                self.model.user_id == user_id
            ).limit(limit).offset(offset).all()
            
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting {self.model_name} by user",
                extra={"user_id": user_id, "error": str(e)}
            )
            raise
    
    def create(self, entity: T) -> T:
        """
        Create new entity.
        
        Args:
            entity: Entity to create
            
        Returns:
            Created entity
        """
        try:
            self.db.add(entity)
            self.db.flush()
            self.db.refresh(entity)
            
            logger.info(
                f"Created {self.model_name}",
                extra={"id": getattr(entity, 'id', None)}
            )
            
            return entity
            
        except SQLAlchemyError as e:
            logger.error(
                f"Database error creating {self.model_name}",
                extra={"error": str(e)}
            )
            self.db.rollback()
            raise
    
    def update(self, entity: T) -> T:
        """
        Update entity.
        
        Args:
            entity: Entity to update
            
        Returns:
            Updated entity
        """
        try:
            self.db.flush()
            self.db.refresh(entity)
            
            logger.info(
                f"Updated {self.model_name}",
                extra={"id": getattr(entity, 'id', None)}
            )
            
            return entity
            
        except SQLAlchemyError as e:
            logger.error(
                f"Database error updating {self.model_name}",
                extra={"error": str(e)}
            )
            self.db.rollback()
            raise
    
    def delete(self, entity: T) -> None:
        """
        Delete entity.
        
        Args:
            entity: Entity to delete
        """
        try:
            entity_id = getattr(entity, 'id', None)
            self.db.delete(entity)
            self.db.flush()
            
            logger.info(
                f"Deleted {self.model_name}",
                extra={"id": entity_id}
            )
            
        except SQLAlchemyError as e:
            logger.error(
                f"Database error deleting {self.model_name}",
                extra={"error": str(e)}
            )
            self.db.rollback()
            raise
    
    def exists(self, id: Any) -> bool:
        """
        Check if entity exists.
        
        Args:
            id: Entity ID
            
        Returns:
            True if exists, False otherwise
        """
        try:
            from backend.core.query_optimizer import QueryOptimizer
            
            return QueryOptimizer.optimize_exists_check(
                self.db,
                self.model,
                {'id': id}
            )
            
        except SQLAlchemyError as e:
            logger.error(
                f"Database error checking {self.model_name} existence",
                extra={"id": id, "error": str(e)}
            )
            raise
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities with optional filters.
        
        Args:
            filters: Optional filter conditions
            
        Returns:
            Count of entities
        """
        try:
            from backend.core.query_optimizer import QueryOptimizer
            
            query = self.db.query(self.model)
            
            if filters:
                for key, value in filters.items():
                    query = query.filter(getattr(self.model, key) == value)
            
            return QueryOptimizer.optimize_count_query(query)
            
        except SQLAlchemyError as e:
            logger.error(
                f"Database error counting {self.model_name}",
                extra={"error": str(e)}
            )
            raise
    
    def commit(self) -> None:
        """Commit transaction."""
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error committing transaction",
                extra={"error": str(e)}
            )
            self.db.rollback()
            raise
    
    def rollback(self) -> None:
        """Rollback transaction."""
        self.db.rollback()


class ServiceError(Exception):
    """Base exception for service errors."""
    
    def __init__(
        self,
        message: str,
        service_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.service_name = service_name
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error": self.__class__.__name__,
            "message": str(self),
            "service": self.service_name,
            "details": self.details
        }

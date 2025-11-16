"""
Batch operations for database performance optimization.

This module provides utilities for efficient batch operations:
- Bulk insert/update/delete
- Batch processing with chunking
- Transaction batching
"""

from typing import List, Dict, Any, Callable, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BatchProcessor(Generic[T]):
    """배치 처리 유틸리티"""
    
    def __init__(self, db: Session, batch_size: int = 100):
        """
        Args:
            db: Database session
            batch_size: Number of items to process in each batch
        """
        self.db = db
        self.batch_size = batch_size
    
    def bulk_insert(self, model_class: type, items: List[Dict[str, Any]]) -> int:
        """
        Bulk insert items efficiently.
        
        Args:
            model_class: SQLAlchemy model class
            items: List of dictionaries with item data
            
        Returns:
            Number of items inserted
        """
        if not items:
            return 0
        
        try:
            total_inserted = 0
            
            # Process in batches
            for i in range(0, len(items), self.batch_size):
                batch = items[i:i + self.batch_size]
                
                # Use bulk_insert_mappings for better performance
                self.db.bulk_insert_mappings(model_class, batch)
                total_inserted += len(batch)
                
                logger.debug(f"Inserted batch {i//self.batch_size + 1}: {len(batch)} items")
            
            self.db.commit()
            logger.info(f"Bulk insert completed: {total_inserted} items")
            return total_inserted
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Bulk insert failed: {e}", exc_info=True)
            raise
    
    def bulk_update(self, model_class: type, items: List[Dict[str, Any]]) -> int:
        """
        Bulk update items efficiently.
        
        Args:
            model_class: SQLAlchemy model class
            items: List of dictionaries with item data (must include 'id')
            
        Returns:
            Number of items updated
        """
        if not items:
            return 0
        
        try:
            total_updated = 0
            
            # Process in batches
            for i in range(0, len(items), self.batch_size):
                batch = items[i:i + self.batch_size]
                
                # Use bulk_update_mappings for better performance
                self.db.bulk_update_mappings(model_class, batch)
                total_updated += len(batch)
                
                logger.debug(f"Updated batch {i//self.batch_size + 1}: {len(batch)} items")
            
            self.db.commit()
            logger.info(f"Bulk update completed: {total_updated} items")
            return total_updated
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Bulk update failed: {e}", exc_info=True)
            raise
    
    def bulk_upsert(
        self,
        model_class: type,
        items: List[Dict[str, Any]],
        constraint_name: str,
        update_columns: List[str]
    ) -> int:
        """
        Bulk upsert (insert or update) items efficiently using PostgreSQL's ON CONFLICT.
        
        Args:
            model_class: SQLAlchemy model class
            items: List of dictionaries with item data
            constraint_name: Name of the unique constraint
            update_columns: Columns to update on conflict
            
        Returns:
            Number of items upserted
        """
        if not items:
            return 0
        
        try:
            total_upserted = 0
            table = model_class.__table__
            
            # Process in batches
            for i in range(0, len(items), self.batch_size):
                batch = items[i:i + self.batch_size]
                
                # Build upsert statement
                stmt = insert(table).values(batch)
                
                # Add ON CONFLICT clause
                update_dict = {col: stmt.excluded[col] for col in update_columns}
                stmt = stmt.on_conflict_do_update(
                    constraint=constraint_name,
                    set_=update_dict
                )
                
                self.db.execute(stmt)
                total_upserted += len(batch)
                
                logger.debug(f"Upserted batch {i//self.batch_size + 1}: {len(batch)} items")
            
            self.db.commit()
            logger.info(f"Bulk upsert completed: {total_upserted} items")
            return total_upserted
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Bulk upsert failed: {e}", exc_info=True)
            raise
    
    def process_in_batches(
        self,
        items: List[T],
        processor: Callable[[List[T]], None]
    ) -> int:
        """
        Process items in batches with a custom processor function.
        
        Args:
            items: List of items to process
            processor: Function that processes a batch of items
            
        Returns:
            Number of items processed
        """
        if not items:
            return 0
        
        try:
            total_processed = 0
            
            for i in range(0, len(items), self.batch_size):
                batch = items[i:i + self.batch_size]
                
                # Process batch
                processor(batch)
                total_processed += len(batch)
                
                logger.debug(f"Processed batch {i//self.batch_size + 1}: {len(batch)} items")
            
            logger.info(f"Batch processing completed: {total_processed} items")
            return total_processed
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}", exc_info=True)
            raise


def bulk_delete_by_ids(
    db: Session,
    model_class: type,
    ids: List[Any],
    batch_size: int = 100
) -> int:
    """
    Bulk delete items by IDs efficiently.
    
    Args:
        db: Database session
        model_class: SQLAlchemy model class
        ids: List of IDs to delete
        batch_size: Number of items to delete in each batch
        
    Returns:
        Number of items deleted
    """
    if not ids:
        return 0
    
    try:
        total_deleted = 0
        
        # Process in batches
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            
            # Delete batch
            deleted = db.query(model_class)\
                .filter(model_class.id.in_(batch_ids))\
                .delete(synchronize_session=False)
            
            total_deleted += deleted
            logger.debug(f"Deleted batch {i//batch_size + 1}: {deleted} items")
        
        db.commit()
        logger.info(f"Bulk delete completed: {total_deleted} items")
        return total_deleted
        
    except Exception as e:
        db.rollback()
        logger.error(f"Bulk delete failed: {e}", exc_info=True)
        raise


def chunked_query(
    query,
    chunk_size: int = 1000
):
    """
    Generator that yields query results in chunks to avoid loading everything into memory.
    
    Args:
        query: SQLAlchemy query object
        chunk_size: Number of items per chunk
        
    Yields:
        Chunks of query results
    """
    offset = 0
    
    while True:
        chunk = query.limit(chunk_size).offset(offset).all()
        
        if not chunk:
            break
        
        yield chunk
        offset += chunk_size
        
        logger.debug(f"Yielded chunk: {len(chunk)} items (offset: {offset})")


# Example usage functions

def example_bulk_insert_executions(db: Session, executions_data: List[Dict[str, Any]]):
    """Example: Bulk insert workflow executions"""
    from backend.db.models.agent_builder import WorkflowExecution
    
    processor = BatchProcessor(db, batch_size=100)
    return processor.bulk_insert(WorkflowExecution, executions_data)


def example_bulk_update_agent_stats(db: Session, stats_data: List[Dict[str, Any]]):
    """Example: Bulk update agent statistics"""
    from backend.db.models.agent_builder import AgentExecutionStats
    
    processor = BatchProcessor(db, batch_size=50)
    return processor.bulk_update(AgentExecutionStats, stats_data)


def example_bulk_upsert_memories(db: Session, memories_data: List[Dict[str, Any]]):
    """Example: Bulk upsert agent memories"""
    from backend.db.models.agent_builder import AgentMemory
    
    processor = BatchProcessor(db, batch_size=100)
    return processor.bulk_upsert(
        AgentMemory,
        memories_data,
        constraint_name='uq_agent_memory_key',  # Adjust to actual constraint
        update_columns=['content', 'importance', 'updated_at']
    )


def example_process_large_dataset(db: Session):
    """Example: Process large dataset in chunks"""
    from backend.db.models.agent_builder import AgentExecution
    
    # Query all executions (don't load into memory)
    query = db.query(AgentExecution).filter(AgentExecution.status == 'completed')
    
    # Process in chunks
    total_processed = 0
    for chunk in chunked_query(query, chunk_size=1000):
        # Process each chunk
        for execution in chunk:
            # Do something with execution
            pass
        
        total_processed += len(chunk)
        logger.info(f"Processed {total_processed} executions so far...")
    
    return total_processed

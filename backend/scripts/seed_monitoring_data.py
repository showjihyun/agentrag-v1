"""
Seed monitoring data for testing
Creates sample query logs and document records
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
import random
import uuid
from sqlalchemy.orm import Session

from backend.db.database import SessionLocal
from backend.models.query_log import QueryLog
from backend.models.document import Document


def seed_query_logs(db: Session, days: int = 7, queries_per_day: int = 50):
    """Seed query logs for the past N days"""
    
    modes = ['fast', 'balanced', 'deep']
    search_types = ['vector', 'keyword', 'hybrid']
    complexity_levels = ['simple', 'medium', 'complex']
    
    print(f"Creating {queries_per_day * days} query logs...")
    
    for day in range(days):
        date = datetime.utcnow() - timedelta(days=day)
        
        for _ in range(queries_per_day):
            # Random time within the day
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            created_at = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Random mode (weighted towards fast)
            mode = random.choices(modes, weights=[0.5, 0.3, 0.2])[0]
            
            # Response time based on mode
            if mode == 'fast':
                response_time = random.uniform(200, 1000)
            elif mode == 'balanced':
                response_time = random.uniform(1000, 3000)
            else:
                response_time = random.uniform(3000, 10000)
            
            # Confidence score (higher for simpler queries)
            confidence = random.uniform(0.5, 0.95)
            
            # Metadata
            metadata = {
                'search_type': random.choice(search_types),
                'complexity_level': random.choice(complexity_levels),
                'search_time_ms': response_time * 0.3,  # Search is ~30% of total time
                'results_count': random.randint(3, 15),
                'cache_hit': random.choice([True, False])
            }
            
            query_log = QueryLog(
                id=uuid.uuid4(),
                query_text=f"Sample query {random.randint(1, 1000)}",
                query_mode=mode,
                response_time_ms=response_time,
                confidence_score=confidence,
                metadata=metadata,
                created_at=created_at
            )
            
            db.add(query_log)
        
        if (day + 1) % 2 == 0:
            db.commit()
            print(f"  ✓ Created logs for day {day + 1}/{days}")
    
    db.commit()
    print(f"✓ Created {queries_per_day * days} query logs")


def seed_documents(db: Session, count: int = 50):
    """Seed sample documents"""
    
    file_types = ['pdf', 'docx', 'txt', 'hwp', 'xlsx']
    statuses = ['completed', 'failed']
    chunking_strategies = ['semantic', 'sentence', 'paragraph']
    
    print(f"Creating {count} documents...")
    
    for i in range(count):
        created_at = datetime.utcnow() - timedelta(days=random.randint(0, 30))
        file_type = random.choice(file_types)
        status = random.choices(statuses, weights=[0.9, 0.1])[0]
        
        # Metadata
        metadata = {
            'processing_time_ms': random.uniform(1000, 10000),
            'chunk_count': random.randint(5, 50),
            'embedding_time_ms': random.uniform(500, 5000),
            'chunking_strategy': random.choice(chunking_strategies)
        }
        
        document = Document(
            id=uuid.uuid4(),
            filename=f"sample_document_{i}.{file_type}",
            file_type=file_type,
            file_size=random.randint(100000, 10000000),  # 100KB to 10MB
            status=status,
            metadata=metadata,
            created_at=created_at,
            updated_at=created_at
        )
        
        db.add(document)
        
        if (i + 1) % 10 == 0:
            db.commit()
            print(f"  ✓ Created {i + 1}/{count} documents")
    
    db.commit()
    print(f"✓ Created {count} documents")


def main():
    """Main seeding function"""
    print("=" * 70)
    print("Seeding Monitoring Data")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Seed query logs
        seed_query_logs(db, days=14, queries_per_day=50)
        
        # Seed documents
        seed_documents(db, count=100)
        
        print("\n" + "=" * 70)
        print("✓ Seeding completed successfully!")
        print("=" * 70)
        print("\nYou can now view the monitoring dashboard at:")
        print("  http://localhost:3000/monitoring/stats")
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

"""
Quick check of monitoring data in DB
"""
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

import sys
sys.path.insert(0, os.path.abspath('.'))

from sqlalchemy import create_engine, text
from backend.config import settings

# Create engine
engine = create_engine(settings.DATABASE_URL)

print("\n" + "="*60)
print("Monitoring Data Check")
print("="*60)

with engine.connect() as conn:
    # Check file uploads
    result = conn.execute(text("SELECT COUNT(*) FROM file_upload_stats"))
    file_count = result.scalar()
    print(f"\n1. File Upload Stats: {file_count} records")
    
    # Check embeddings
    result = conn.execute(text("SELECT COUNT(*) FROM embedding_stats"))
    emb_count = result.scalar()
    print(f"2. Embedding Stats: {emb_count} records")
    
    # Check hybrid search
    result = conn.execute(text("SELECT COUNT(*) FROM hybrid_search_stats"))
    search_count = result.scalar()
    print(f"3. Hybrid Search Stats: {search_count} records")
    
    # Check RAG processing
    result = conn.execute(text("SELECT COUNT(*) FROM rag_processing_stats"))
    rag_count = result.scalar()
    print(f"4. RAG Processing Stats: {rag_count} records")
    
    # Check daily trends
    result = conn.execute(text("SELECT COUNT(*) FROM daily_accuracy_trends"))
    trend_count = result.scalar()
    print(f"5. Daily Accuracy Trends: {trend_count} records")
    
    # Get latest RAG stats
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            AVG(confidence_score) as avg_conf,
            AVG(response_time_ms) as avg_time,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
        FROM rag_processing_stats
        WHERE created_at >= NOW() - INTERVAL '7 days'
    """))
    row = result.fetchone()
    if row:
        print(f"\nRAG Stats (Last 7 days):")
        print(f"  - Total queries: {row[0]}")
        avg_conf = row[1] if row[1] else 0
        avg_time = row[2] if row[2] else 0
        success_rate = (row[3]/row[0]*100 if row[0] > 0 else 0)
        print(f"  - Avg confidence: {avg_conf:.3f}")
        print(f"  - Avg response time: {avg_time:.1f} ms")
        print(f"  - Success rate: {success_rate:.1f}%")

print("\n" + "="*60)
print("All monitoring data is stored in DB!")
print("="*60)
print("\nYou can view it at:")
print("  http://localhost:3000/monitoring/stats")
print("\nOr test the API:")
print("  curl http://localhost:8000/api/monitoring/stats/overview?days=7")
print("="*60 + "\n")

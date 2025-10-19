"""
Test monitoring statistics - Insert sample data and verify
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.db.database import get_db
from backend.services.monitoring_service import MonitoringService
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def insert_sample_data():
    """Insert sample monitoring data"""
    
    db = next(get_db())
    service = MonitoringService(db)
    
    print("\n" + "="*60)
    print("샘플 모니터링 데이터 삽입")
    print("="*60)
    
    # 1. 파일 업로드 통계
    print("\n1. 파일 업로드 통계 삽입...")
    file_types = ['pdf', 'docx', 'txt', 'xlsx', 'pptx']
    statuses = ['completed', 'completed', 'completed', 'failed']  # 75% success rate
    
    for i in range(20):
        file_type = random.choice(file_types)
        status = random.choice(statuses)
        
        service.save_file_upload_stat(
            file_id=f"file_{i+1}",
            filename=f"document_{i+1}.{file_type}",
            file_type=file_type,
            file_size_mb=round(random.uniform(0.5, 10.0), 2),
            status=status,
            processing_time_ms=round(random.uniform(500, 3000), 1) if status == 'completed' else None,
            error_message="Processing failed" if status == 'failed' else None
        )
    
    print(f"   ✅ 20개 파일 업로드 통계 삽입 완료")
    
    # 2. 임베딩 통계
    print("\n2. 임베딩 통계 삽입...")
    strategies = ['fixed', 'semantic', 'hybrid']
    
    for i in range(15):
        service.save_embedding_stat(
            document_id=f"doc_{i+1}",
            embedding_model="jhgan/ko-sroberta-multitask",
            total_chunks=random.randint(10, 100),
            chunking_strategy=random.choice(strategies),
            embedding_time_ms=round(random.uniform(1000, 5000), 1)
        )
    
    print(f"   ✅ 15개 임베딩 통계 삽입 완료")
    
    # 3. 하이브리드 검색 통계
    print("\n3. 하이브리드 검색 통계 삽입...")
    search_types = ['vector_only', 'keyword_only', 'hybrid']
    
    for i in range(50):
        service.save_hybrid_search_stat(
            session_id=f"session_{i % 10}",
            search_type=random.choice(search_types),
            query_text=f"Sample query {i+1}",
            results_count=random.randint(1, 10),
            search_time_ms=round(random.uniform(50, 500), 1),
            cache_hit=random.choice([True, False])
        )
    
    print(f"   ✅ 50개 검색 통계 삽입 완료")
    
    # 4. RAG 처리 통계 (가장 중요!)
    print("\n4. RAG 처리 통계 삽입...")
    modes = ['auto', 'fast', 'balanced', 'deep']
    complexities = ['simple', 'medium', 'complex']
    
    for i in range(100):
        confidence = round(random.uniform(0.5, 0.95), 3)
        success = random.choice([True, True, True, False])  # 75% success
        
        token_usage = {
            "input": random.randint(2000, 4000),
            "output": random.randint(300, 700),
            "total": 0
        }
        token_usage["total"] = token_usage["input"] + token_usage["output"]
        token_usage["estimated_cost"] = round(token_usage["total"] / 1000000 * 0.5, 6)
        
        quality_scores = {
            "overall_score": round(random.uniform(0.7, 0.95), 2),
            "relevance": round(random.uniform(0.75, 0.95), 2),
            "accuracy": round(random.uniform(0.75, 0.95), 2),
            "completeness": round(random.uniform(0.70, 0.90), 2),
            "clarity": round(random.uniform(0.75, 0.92), 2),
            "source_citation": round(random.uniform(0.80, 0.95), 2)
        }
        
        service.save_rag_processing_stat(
            session_id=f"session_{i % 20}",
            query_text=f"Sample RAG query {i+1}",
            mode=random.choice(modes),
            complexity=random.choice(complexities),
            response_time_ms=round(random.uniform(1000, 5000), 1),
            confidence_score=confidence if success else None,
            success=success,
            error_message="Processing error" if not success else None,
            token_usage=token_usage if success else None,
            quality_scores=quality_scores if success else None
        )
    
    print(f"   ✅ 100개 RAG 처리 통계 삽입 완료")
    
    # 5. 일일 트렌드는 자동으로 업데이트됨
    print("\n5. 일일 트렌드 자동 업데이트 확인...")
    trends = service.get_daily_trends(days=7)
    print(f"   ✅ {len(trends)}개 일일 트렌드 레코드 확인")
    
    print("\n" + "="*60)
    print("✅ 샘플 데이터 삽입 완료!")
    print("="*60)


def verify_data():
    """Verify inserted data"""
    
    db = next(get_db())
    service = MonitoringService(db)
    
    print("\n" + "="*60)
    print("데이터 확인")
    print("="*60)
    
    # 1. 파일 업로드 통계
    print("\n1. 파일 업로드 통계")
    file_stats = service.get_file_upload_stats(days=7)
    print(f"   총 파일: {file_stats['total_files']}")
    print(f"   성공: {file_stats['successful_uploads']}")
    print(f"   실패: {file_stats['failed_uploads']}")
    print(f"   총 크기: {file_stats['total_size_mb']:.2f} MB")
    print(f"   평균 처리 시간: {file_stats['avg_processing_time_ms']:.1f} ms")
    print(f"   파일 타입별:")
    for ft, count in file_stats['by_file_type'].items():
        print(f"      - {ft}: {count}개")
    
    # 2. 임베딩 통계
    print("\n2. 임베딩 통계")
    emb_stats = service.get_embedding_stats(days=7)
    print(f"   총 임베딩: {emb_stats['total_embeddings']}")
    print(f"   총 청크: {emb_stats['total_chunks']}")
    print(f"   평균 청크/문서: {emb_stats['avg_chunks_per_document']:.1f}")
    print(f"   임베딩 모델: {emb_stats['embedding_model']}")
    print(f"   평균 시간: {emb_stats['avg_embedding_time_ms']:.1f} ms")
    
    # 3. 하이브리드 검색 통계
    print("\n3. 하이브리드 검색 통계")
    search_stats = service.get_hybrid_search_stats(days=7)
    print(f"   총 검색: {search_stats['total_searches']}")
    print(f"   Vector Only: {search_stats['vector_only']}")
    print(f"   Keyword Only: {search_stats['keyword_only']}")
    print(f"   Hybrid: {search_stats['hybrid']}")
    print(f"   평균 시간: {search_stats['avg_search_time_ms']:.1f} ms")
    print(f"   평균 결과 수: {search_stats['avg_results_count']:.1f}")
    print(f"   캐시 히트율: {search_stats['cache_hit_rate']*100:.1f}%")
    
    # 4. RAG 처리 통계
    print("\n4. RAG 처리 통계")
    rag_stats = service.get_rag_processing_stats(days=7)
    print(f"   총 쿼리: {rag_stats['total_queries']}")
    print(f"   모드별:")
    for mode, count in rag_stats['by_mode'].items():
        print(f"      - {mode}: {count}개")
    print(f"   복잡도별:")
    for comp, count in rag_stats['by_complexity'].items():
        print(f"      - {comp}: {count}개")
    print(f"   평균 응답 시간: {rag_stats['avg_response_time_ms']:.1f} ms")
    print(f"   평균 신뢰도: {rag_stats['avg_confidence_score']:.3f}")
    print(f"   성공률: {rag_stats['success_rate']*100:.1f}%")
    
    # 5. 일일 트렌드
    print("\n5. 일일 트렌드")
    trends = service.get_daily_trends(days=7)
    print(f"   트렌드 레코드: {len(trends)}개")
    if trends:
        latest = trends[-1]
        print(f"   최신 날짜: {latest['date']}")
        print(f"   총 쿼리: {latest['total_queries']}")
        print(f"   평균 신뢰도: {latest['avg_confidence']:.3f}")
        print(f"   성공률: {latest['success_rate']*100:.1f}%")
    
    print("\n" + "="*60)
    print("✅ 데이터 확인 완료!")
    print("="*60)
    
    # 6. API 테스트 안내
    print("\n" + "="*60)
    print("API 테스트")
    print("="*60)
    print("\n다음 명령어로 API를 테스트하세요:")
    print("\n1. 전체 통계:")
    print("   curl http://localhost:8000/api/monitoring/stats/overview?days=7")
    print("\n2. RAG 처리 통계:")
    print("   curl http://localhost:8000/api/monitoring/stats/rag-processing?days=7")
    print("\n3. 일일 트렌드:")
    print("   curl http://localhost:8000/api/monitoring/stats/daily-trends?days=7")
    print("\n4. 프론트엔드:")
    print("   http://localhost:3000/monitoring/stats")
    print("\n" + "="*60)


def check_tables():
    """Check if tables exist"""
    from sqlalchemy import text
    from backend.db.database import engine
    
    print("\n" + "="*60)
    print("테이블 확인")
    print("="*60)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
            AND (table_name LIKE '%_stats' OR table_name LIKE '%_trends')
            ORDER BY table_name
        """))
        
        tables = list(result)
        
        if not tables:
            print("\n❌ 모니터링 테이블이 없습니다!")
            print("\n다음 명령어로 테이블을 생성하세요:")
            print("   python backend/scripts/create_monitoring_tables.py")
            return False
        
        print(f"\n✅ {len(tables)}개 테이블 발견:")
        for table_name, col_count in tables:
            # Get row count
            count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            row_count = count_result.scalar()
            print(f"   - {table_name}: {col_count}개 컬럼, {row_count}개 레코드")
        
        return True


def main():
    """Main function"""
    
    print("\n" + "="*60)
    print("모니터링 통계 테스트")
    print("="*60)
    
    # 1. 테이블 확인
    if not check_tables():
        return
    
    # 2. 샘플 데이터 삽입
    try:
        insert_sample_data()
    except Exception as e:
        logger.error(f"샘플 데이터 삽입 실패: {e}", exc_info=True)
        return
    
    # 3. 데이터 확인
    try:
        verify_data()
    except Exception as e:
        logger.error(f"데이터 확인 실패: {e}", exc_info=True)
        return
    
    print("\n✅ 모든 테스트 완료!")
    print("\n이제 http://localhost:3000/monitoring/stats 에서 데이터를 확인할 수 있습니다!")


if __name__ == "__main__":
    main()

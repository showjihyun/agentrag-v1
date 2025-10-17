"""
ColPali 진단 스크립트

이미지 검색이 작동하지 않을 때 문제를 진단합니다.
"""

import asyncio
import sys
import os

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)


async def diagnose():
    print("=" * 60)
    print("ColPali 진단 시작")
    print("=" * 60)
    
    # 1. 설정 확인
    print("\n1. 설정 확인")
    try:
        from backend.config import settings
        
        print(f"   ENABLE_COLPALI: {settings.ENABLE_COLPALI}")
        print(f"   ENABLE_HYBRID_PROCESSING: {settings.ENABLE_HYBRID_PROCESSING}")
        print(f"   COLPALI_MODEL: {settings.COLPALI_MODEL}")
        print(f"   HYBRID_COLPALI_THRESHOLD: {settings.HYBRID_COLPALI_THRESHOLD}")
        print(f"   HYBRID_PROCESS_IMAGES_ALWAYS: {settings.HYBRID_PROCESS_IMAGES_ALWAYS}")
        
        if not settings.ENABLE_COLPALI:
            print(f"   ⚠️  경고: ENABLE_COLPALI=False. .env에서 True로 설정하세요.")
            
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return
    
    # 2. ColPali 프로세서 확인
    print("\n2. ColPali 프로세서 확인")
    processor = None
    try:
        from backend.services.colpali_processor import get_colpali_processor
        
        processor = get_colpali_processor()
        if processor and processor.is_available():
            print(f"   ✅ ColPali 프로세서 초기화됨")
            info = processor.get_model_info()
            print(f"   모델: {info['model_name']}")
            print(f"   디바이스: {info['device']}")
            print(f"   GPU 사용: {info['gpu_used']}")
            print(f"   바이너리화: {info['binarization']}")
            print(f"   풀링: {info['pooling']}")
        else:
            print(f"   ❌ ColPali 프로세서 사용 불가")
            print(f"   해결: pip install colpali-engine")
            return
    except ImportError as e:
        print(f"   ❌ ColPali 모듈 없음: {e}")
        print(f"   해결: pip install colpali-engine")
        return
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return
    
    # 3. Milvus 컬렉션 확인
    print("\n3. Milvus 컬렉션 확인")
    service = None
    try:
        from backend.services.colpali_milvus_service import get_colpali_milvus_service
        
        service = get_colpali_milvus_service(
            host=settings.MILVUS_HOST,
            port=str(settings.MILVUS_PORT)
        )
        
        stats = service.get_collection_stats()
        print(f"   ✅ 컬렉션: {stats['name']}")
        print(f"   패치 수: {stats['num_entities']}")
        
        if stats['num_entities'] == 0:
            print(f"   ⚠️  경고: 데이터가 없습니다.")
            print(f"   해결: 문서를 업로드하세요.")
            print(f"   - PDF 파일을 /api/documents/upload로 업로드")
            print(f"   - 로그에서 'ColPali processing completed' 확인")
            return
        else:
            print(f"   ✅ {stats['num_entities']}개의 패치가 저장되어 있습니다.")
            
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        print(f"   해결: Milvus가 실행 중인지 확인하세요.")
        print(f"   docker-compose up -d milvus")
        return
    
    # 4. 검색 테스트
    print("\n4. 검색 테스트")
    try:
        query = "장비준비"
        print(f"   쿼리: '{query}'")
        
        # 쿼리 임베딩
        print(f"   쿼리 임베딩 생성 중...")
        query_embeddings = processor.process_text_query(query)
        print(f"   ✅ 쿼리 임베딩 생성: {query_embeddings.shape}")
        
        # 검색
        print(f"   검색 중...")
        results = service.search_images(query_embeddings, top_k=5)
        print(f"   ✅ 검색 완료: {len(results)}개 결과")
        
        if len(results) > 0:
            print(f"\n   상위 결과:")
            for i, result in enumerate(results[:3]):
                image_id = result.get('image_id', 'unknown')
                score = result.get('score', 0.0)
                doc_id = result.get('document_id', 'unknown')
                print(f"   {i+1}. Score: {score:.4f}")
                print(f"      Image ID: {image_id[:16]}...")
                print(f"      Document ID: {doc_id[:16]}...")
        else:
            print(f"   ⚠️  경고: 검색 결과가 없습니다.")
            print(f"\n   가능한 원인:")
            print(f"   1. 문서가 ColPali로 처리되지 않음")
            print(f"      → 로그에서 'method=colpali_only' 또는 'method=hybrid' 확인")
            print(f"   2. 쿼리와 문서 내용이 관련 없음")
            print(f"      → 다른 쿼리로 테스트")
            print(f"   3. 임계값이 너무 높음")
            print(f"      → HYBRID_COLPALI_THRESHOLD를 0.5로 증가")
            
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. VectorSearchAgent 확인
    print("\n5. VectorSearchAgent 통합 확인")
    try:
        from backend.agents.vector_search import VectorSearchAgent
        from backend.services.milvus import MilvusManager
        from backend.services.embedding import EmbeddingService
        
        # 에이전트 초기화
        milvus_manager = MilvusManager(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            collection_name=settings.MILVUS_COLLECTION_NAME,
            embedding_dim=128  # 임시
        )
        
        embedding_service = EmbeddingService()
        
        agent = VectorSearchAgent(
            milvus_manager=milvus_manager,
            embedding_service=embedding_service,
            colpali_processor=processor,
            colpali_milvus=service,
            enable_colpali_search=True
        )
        
        print(f"   ✅ VectorSearchAgent 초기화됨")
        print(f"   ColPali 검색: {agent.use_colpali}")
        
        if not agent.use_colpali:
            print(f"   ⚠️  경고: ColPali 검색이 비활성화되어 있습니다.")
            print(f"   해결: enable_colpali_search=True로 설정")
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("진단 완료")
    print("=" * 60)
    
    # 요약
    print("\n📋 요약:")
    if processor and processor.is_available():
        print("   ✅ ColPali 프로세서: 정상")
    else:
        print("   ❌ ColPali 프로세서: 문제")
        
    if service and stats['num_entities'] > 0:
        print("   ✅ Milvus 데이터: 정상")
    else:
        print("   ❌ Milvus 데이터: 없음")
        
    if len(results) > 0:
        print("   ✅ 검색 기능: 정상")
    else:
        print("   ⚠️  검색 기능: 결과 없음")
    
    print("\n💡 다음 단계:")
    if not processor or not processor.is_available():
        print("   1. ColPali 설치: pip install colpali-engine")
    elif not service or stats['num_entities'] == 0:
        print("   1. 문서 업로드: PDF 파일을 /api/documents/upload로 업로드")
        print("   2. 로그 확인: 'ColPali processing completed' 메시지 확인")
    elif len(results) == 0:
        print("   1. 다른 쿼리로 테스트")
        print("   2. 임계값 조정: HYBRID_COLPALI_THRESHOLD=0.5")
        print("   3. 항상 하이브리드: HYBRID_PROCESS_IMAGES_ALWAYS=True")
    else:
        print("   ✅ 모든 기능이 정상 작동합니다!")
        print("   문제가 계속되면 백엔드 로그를 확인하세요.")


if __name__ == "__main__":
    asyncio.run(diagnose())

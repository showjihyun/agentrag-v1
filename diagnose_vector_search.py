"""
벡터 검색이 작동하지 않는 이유를 진단하는 스크립트
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.config import settings
from pymilvus import connections, Collection


async def diagnose_vector_search():
    """벡터 검색 문제 진단"""
    
    print("=" * 70)
    print("벡터 검색 진단")
    print("=" * 70)
    
    try:
        # 1. Embedding Service 초기화
        print("\n1. Embedding Service 확인...")
        embedding_service = EmbeddingService()
        print(f"   모델: {embedding_service.model_name}")
        print(f"   차원: {embedding_service.dimension}")
        
        # 2. 테스트 쿼리 임베딩
        print("\n2. 테스트 쿼리 임베딩...")
        test_query = "빅밸류의 주소는?"
        query_embedding = await embedding_service.embed_text(test_query)
        print(f"   쿼리: {test_query}")
        print(f"   임베딩 차원: {len(query_embedding)}")
        print(f"   임베딩 샘플: {query_embedding[:5]}")
        
        # 3. Milvus 연결
        print("\n3. Milvus 연결...")
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        collection = Collection("documents")
        print(f"   Collection: documents")

        print(f"   엔티티 수: {collection.num_entities}")
        
        # 4. 스키마 확인
        print("\n4. 스키마 확인...")
        schema = collection.schema
        for field in schema.fields:
            if field.dtype.name == "FLOAT_VECTOR":
                stored_dim = field.params.get('dim')
                print(f"   벡터 필드: {field.name}")
                print(f"   저장된 차원: {stored_dim}")
                
                if stored_dim != len(query_embedding):
                    print(f"\n   ❌ 차원 불일치 발견!")
                    print(f"   현재 임베딩 모델: {len(query_embedding)}차원")
                    print(f"   Milvus 저장 데이터: {stored_dim}차원")
                    print(f"\n   이것이 검색 실패의 원인입니다!")
                    return False
                else:
                    print(f"   ✅ 차원 일치: {stored_dim}차원")
        
        # 5. 직접 벡터 검색 테스트
        print("\n5. 직접 벡터 검색 테스트...")
        
        search_params = {
            "metric_type": "COSINE",
            "params": {"ef": 64}
        }
        
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=5,
            output_fields=["document_name", "text"]
        )
        
        if not results or len(results[0]) == 0:
            print("   ❌ 검색 결과 없음!")
            print("\n   가능한 원인:")
            print("   1. Collection이 로드되지 않음")
            print("   2. 임베딩 모델이 변경됨")
            print("   3. 벡터 데이터가 손상됨")
            return False
        
        print(f"   ✅ {len(results[0])}개 결과 발견!")
        
        # 6. 결과 분석
        print("\n6. 검색 결과:")
        for i, hit in enumerate(results[0], 1):
            print(f"\n   [{i}] Score: {hit.score:.4f}")
            doc_name = hit.entity.get('document_name') if hasattr(hit.entity, 'get') else getattr(hit.entity, 'document_name', 'Unknown')
            text = hit.entity.get('text') if hasattr(hit.entity, 'get') else getattr(hit.entity, 'text', '')
            print(f"       Document: {doc_name}")
            print(f"       Text: {text[:100]}..." if len(text) > 100 else f"       Text: {text}")
        
        print("\n" + "=" * 70)
        print("✅ 진단 완료")
        print("=" * 70)
        
        if len(results[0]) > 0:
            print("\n벡터 검색이 정상 작동합니다!")
            print("API에서 검색이 안 되는 것은 다른 문제일 수 있습니다.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            connections.disconnect("default")
        except:
            pass


if __name__ == "__main__":
    success = asyncio.run(diagnose_vector_search())
    sys.exit(0 if success else 1)

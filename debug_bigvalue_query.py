"""
빅밸류 주소 검색 문제 디버깅 스크립트

"빅밸류의 주소는?" 질의가 왜 제대로 작동하지 않는지 분석
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.config import settings


async def check_document_exists():
    """문서가 Milvus에 존재하는지 확인"""
    
    print("\n" + "=" * 80)
    print("📄 Step 1: 문서 존재 확인")
    print("=" * 80 + "\n")
    
    try:
        # Milvus 연결
        from pymilvus import connections, Collection
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        
        # 컬렉션 정보 확인
        collection_name = settings.MILVUS_COLLECTION_NAME
        print(f"컬렉션 이름: {collection_name}")
        
        # 전체 문서 수 확인
        collection = Collection(collection_name)
        collection.load()
        
        num_entities = collection.num_entities
        print(f"총 문서 청크 수: {num_entities}")
        
        if num_entities == 0:
            print("❌ 문서가 하나도 없습니다! 먼저 문서를 업로드하세요.")
            return False
        
        # "시험합의서" 관련 문서 검색
        print("\n'시험합의서' 키워드로 검색 중...")
        
        embedding_service = EmbeddingService()
        query_vector = await embedding_service.embed_text("시험합의서")
        
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=10,
            output_fields=["document_id", "document_name", "text", "metadata"]
        )
        
        print(f"\n검색 결과: {len(results[0])} 개")
        
        found_target = False
        for i, hit in enumerate(results[0], 1):
            doc_name = hit.entity.get('document_name', 'Unknown')
            text_preview = hit.entity.get('text', '')[:100]
            score = hit.score
            
            print(f"\n[{i}] {doc_name}")
            print(f"    점수: {score:.4f}")
            print(f"    내용: {text_preview}...")
            
            if "GS-A-25-0127" in doc_name or "시험합의서" in doc_name:
                found_target = True
                print("    ✅ 타겟 문서 발견!")
        
        if not found_target:
            print("\n❌ 'GS-A-25-0127 시험합의서' 문서를 찾을 수 없습니다.")
            print("   문서가 업로드되지 않았거나 다른 이름으로 저장되었을 수 있습니다.")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bigvalue_query():
    """'빅밸류의 주소는?' 질의 테스트"""
    
    print("\n" + "=" * 80)
    print("🔍 Step 2: '빅밸류의 주소는?' 질의 테스트")
    print("=" * 80 + "\n")
    
    query = "빅밸류의 주소는?"
    print(f"질의: {query}")
    print()
    
    try:
        # 임베딩 생성
        embedding_service = EmbeddingService()
        query_vector = await embedding_service.embed_text(query)
        
        print(f"✅ 임베딩 생성 완료 (차원: {len(query_vector)})")
        
        # Milvus 검색
        from pymilvus import connections, Collection
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        
        collection_name = settings.MILVUS_COLLECTION_NAME
        collection = Collection(collection_name)
        collection.load()
        
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=10,
            output_fields=["document_id", "document_name", "text", "metadata"]
        )
        
        print(f"\n검색 결과: {len(results[0])} 개")
        print()
        
        # 결과 분석
        for i, hit in enumerate(results[0], 1):
            doc_name = hit.entity.get('document_name', 'Unknown')
            text = hit.entity.get('text', '')
            score = hit.score
            
            print(f"[{i}] {doc_name}")
            print(f"    점수: {score:.4f}")
            print(f"    내용 길이: {len(text)} 자")
            
            # "빅밸류" 또는 "주소" 키워드 확인
            has_bigvalue = "빅밸류" in text or "Big Value" in text or "빅 밸류" in text
            has_address = "주소" in text or "address" in text.lower()
            
            if has_bigvalue:
                print(f"    ✅ '빅밸류' 키워드 발견!")
            if has_address:
                print(f"    ✅ '주소' 키워드 발견!")
            
            # 내용 미리보기
            if has_bigvalue or has_address:
                print(f"    내용: {text[:200]}...")
            else:
                print(f"    내용: {text[:100]}...")
            
            print()
        
        # 최상위 결과 분석
        if len(results[0]) > 0:
            top_hit = results[0][0]
            top_text = top_hit.entity.get('text', '')
            top_score = top_hit.score
            
            print("\n" + "-" * 80)
            print("📊 최상위 결과 분석")
            print("-" * 80)
            print(f"점수: {top_score:.4f}")
            print(f"'빅밸류' 포함: {'빅밸류' in top_text or 'Big Value' in top_text}")
            print(f"'주소' 포함: {'주소' in top_text}")
            print()
            
            if top_score < 0.3:
                print("⚠️  최상위 결과의 점수가 매우 낮습니다 (< 0.3)")
                print("   임베딩 모델이 질의를 제대로 이해하지 못했을 수 있습니다.")
            
            if "빅밸류" not in top_text and "Big Value" not in top_text:
                print("❌ 최상위 결과에 '빅밸류' 키워드가 없습니다!")
                print("   가능한 원인:")
                print("   1. 문서에 '빅밸류'가 다른 형태로 표기됨 (예: Big-Value, 빅 밸류)")
                print("   2. 임베딩 모델이 '빅밸류'를 제대로 인식하지 못함")
                print("   3. 문서가 제대로 청킹되지 않아 주소 정보가 분리됨")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


async def test_alternative_queries():
    """대체 질의 테스트"""
    
    print("\n" + "=" * 80)
    print("🔄 Step 3: 대체 질의 테스트")
    print("=" * 80 + "\n")
    
    alternative_queries = [
        "빅밸류 주소",
        "Big Value 주소",
        "빅밸류 위치",
        "시험 장소",
        "시험 수행 장소",
        "GS-A-25-0127 시험 장소"
    ]
    
    embedding_service = EmbeddingService()
    
    from pymilvus import connections, Collection
    connections.connect(
        alias="default",
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT
    )
    
    collection_name = settings.MILVUS_COLLECTION_NAME
    collection = Collection(collection_name)
    collection.load()
    
    for query in alternative_queries:
        print(f"\n질의: '{query}'")
        
        try:
            query_vector = await embedding_service.embed_text(query)
            
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            results = collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=3,
                output_fields=["document_name", "text"]
            )
            
            if len(results[0]) > 0:
                top_hit = results[0][0]
                top_text = top_hit.entity.get('text', '')
                top_score = top_hit.score
                
                has_bigvalue = "빅밸류" in top_text or "Big Value" in top_text
                has_address = "주소" in top_text
                
                print(f"  최상위 점수: {top_score:.4f}")
                print(f"  빅밸류 포함: {has_bigvalue}")
                print(f"  주소 포함: {has_address}")
                
                if has_bigvalue and has_address:
                    print(f"  ✅ 좋은 결과!")
                    print(f"  내용: {top_text[:150]}...")
        
        except Exception as e:
            print(f"  ❌ 오류: {e}")


async def check_document_content():
    """문서 내용 직접 확인"""
    
    print("\n" + "=" * 80)
    print("📖 Step 4: 문서 내용 직접 확인")
    print("=" * 80 + "\n")
    
    try:
        from pymilvus import connections, Collection
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        
        collection_name = settings.MILVUS_COLLECTION_NAME
        collection = Collection(collection_name)
        collection.load()
        
        # 모든 문서 가져오기 (최대 100개)
        print("문서 청크 샘플링 중...")
        
        # 간단한 쿼리로 모든 문서 가져오기
        embedding_service = EmbeddingService()
        dummy_vector = await embedding_service.embed_text("문서")
        
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = collection.search(
            data=[dummy_vector],
            anns_field="embedding",
            param=search_params,
            limit=100,
            output_fields=["document_name", "text"]
        )
        
        # "빅밸류" 키워드 검색
        print("\n'빅밸류' 키워드가 포함된 청크 검색 중...")
        
        found_chunks = []
        for hit in results[0]:
            text = hit.entity.get('text', '')
            doc_name = hit.entity.get('document_name', '')
            
            if "빅밸류" in text or "Big Value" in text or "빅 밸류" in text:
                found_chunks.append({
                    'doc_name': doc_name,
                    'text': text
                })
        
        if found_chunks:
            print(f"\n✅ '빅밸류' 키워드가 포함된 청크 {len(found_chunks)}개 발견!")
            
            for i, chunk in enumerate(found_chunks[:3], 1):
                print(f"\n[{i}] {chunk['doc_name']}")
                print(f"    {chunk['text'][:300]}...")
                
                # 주소 정보 확인
                if "주소" in chunk['text']:
                    print(f"    ✅ 주소 정보도 포함됨!")
        else:
            print("\n❌ '빅밸류' 키워드가 포함된 청크를 찾을 수 없습니다!")
            print("   가능한 원인:")
            print("   1. 문서가 업로드되지 않음")
            print("   2. PDF 파싱 오류로 텍스트 추출 실패")
            print("   3. '빅밸류'가 다른 형태로 표기됨")
            
            # 시험합의서 문서 확인
            print("\n'시험합의서' 문서 확인 중...")
            for hit in results[0][:20]:
                doc_name = hit.entity.get('document_name', '')
                if "시험합의서" in doc_name or "GS-A-25-0127" in doc_name:
                    text = hit.entity.get('text', '')
                    print(f"\n문서명: {doc_name}")
                    print(f"내용 샘플: {text[:300]}...")
                    break
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


async def suggest_solutions():
    """해결 방안 제시"""
    
    print("\n" + "=" * 80)
    print("💡 Step 5: 해결 방안")
    print("=" * 80 + "\n")
    
    print("문제 해결을 위한 제안:")
    print()
    print("1. 문서 재업로드")
    print("   - PDF 파일을 다시 업로드하여 텍스트 추출 확인")
    print()
    print("2. 청킹 전략 개선")
    print("   - 청크 크기를 늘려서 주소 정보가 분리되지 않도록 함")
    print("   - 오버랩을 늘려서 문맥 보존")
    print()
    print("3. 키워드 검색 추가")
    print("   - 하이브리드 검색 활성화 (벡터 + 키워드)")
    print("   - BM25 검색 추가")
    print()
    print("4. 쿼리 확장")
    print("   - '빅밸류의 주소는?' → '빅밸류 주소', 'Big Value 주소' 등")
    print("   - 동의어 처리")
    print()
    print("5. 리랭킹 강화")
    print("   - Cross-encoder 리랭커 활용")
    print("   - 키워드 매칭 가중치 증가")


async def main():
    """전체 디버깅 프로세스 실행"""
    
    print("\n" + "🔍" * 40)
    print("   빅밸류 주소 검색 문제 디버깅")
    print("🔍" * 40)
    
    # Step 1: 문서 존재 확인
    doc_exists = await check_document_exists()
    
    if not doc_exists:
        print("\n⚠️  문서가 존재하지 않거나 찾을 수 없습니다.")
        print("   먼저 'GS-A-25-0127 시험합의서 v0.1(초안).pdf' 파일을 업로드하세요.")
        return
    
    # Step 2: 질의 테스트
    await test_bigvalue_query()
    
    # Step 3: 대체 질의 테스트
    await test_alternative_queries()
    
    # Step 4: 문서 내용 확인
    await check_document_content()
    
    # Step 5: 해결 방안
    await suggest_solutions()
    
    print("\n" + "=" * 80)
    print("✅ 디버깅 완료!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

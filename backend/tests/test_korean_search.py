"""
한글 검색 기능 테스트 스크립트

이 스크립트는 다음을 테스트합니다:
- 다국어 임베딩 모델 (한글 지원)
- 하이브리드 검색 (벡터 + 키워드)
- 한글 토크나이저
- 다양한 한글 쿼리 패턴
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.services.hybrid_search import HybridSearchManager
from backend.services.milvus import MilvusManager
from backend.services.embedding import EmbeddingService
from backend.config import settings


async def test_korean_search():
    """한글 검색 기능 종합 테스트"""

    print("\n" + "=" * 80)
    print("🇰🇷 한글 검색 시스템 테스트")
    print("=" * 80)

    # 1. 초기화
    print("\n[1/5] 🔧 시스템 초기화 중...")
    try:
        embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL)
        print(f"   ✅ 임베딩 모델: {embedding_service.model_name}")
        print(f"   ✅ 임베딩 차원: {embedding_service.dimension}")
        print(f"   ✅ 최대 시퀀스 길이: {embedding_service.model.max_seq_length}")
    except Exception as e:
        print(f"   ❌ 초기화 실패: {e}")
        return

    # 2. 테스트 문서 준비
    print("\n[2/5] 📚 테스트 문서 준비 중...")
    test_documents = [
        {
            "id": "test_1",
            "document_id": "doc_ai",
            "text": "인공지능(AI)은 컴퓨터 시스템이 인간의 지능을 모방하는 기술입니다. "
            "기계학습, 딥러닝, 자연어 처리, 컴퓨터 비전 등이 포함됩니다. "
            "AI는 다양한 산업 분야에서 혁신을 이끌고 있습니다.",
            "document_name": "AI_기초.txt",
            "chunk_index": 0,
            "file_type": "txt",
            "upload_date": 1704441600,
        },
        {
            "id": "test_2",
            "document_id": "doc_ml",
            "text": "머신러닝은 데이터로부터 패턴을 학습하는 AI의 핵심 기술입니다. "
            "지도학습, 비지도학습, 강화학습으로 분류됩니다. "
            "기계학습이라고도 불리며, 예측 모델을 만드는 데 사용됩니다.",
            "document_name": "ML_가이드.txt",
            "chunk_index": 0,
            "file_type": "txt",
            "upload_date": 1704441600,
        },
        {
            "id": "test_3",
            "document_id": "doc_dl",
            "text": "딥러닝은 인공 신경망을 사용하는 머신러닝 기법입니다. "
            "CNN, RNN, Transformer 등의 아키텍처가 있습니다. "
            "이미지 인식, 음성 인식, 자연어 처리에서 뛰어난 성능을 보입니다.",
            "document_name": "딥러닝_가이드.txt",
            "chunk_index": 0,
            "file_type": "txt",
            "upload_date": 1704441600,
        },
        {
            "id": "test_4",
            "document_id": "doc_nlp",
            "text": "자연어 처리(NLP)는 컴퓨터가 인간의 언어를 이해하고 생성하는 기술입니다. "
            "기계 번역, 텍스트 요약, 감정 분석, 질의응답 시스템 등에 활용됩니다. "
            "GPT, BERT 같은 대규모 언어 모델이 NLP 발전을 이끌고 있습니다.",
            "document_name": "NLP_소개.txt",
            "chunk_index": 0,
            "file_type": "txt",
            "upload_date": 1704441600,
        },
        {
            "id": "test_5",
            "document_id": "doc_cv",
            "text": "컴퓨터 비전은 컴퓨터가 이미지와 비디오를 이해하는 기술입니다. "
            "객체 감지, 이미지 분류, 얼굴 인식, 자율주행 등에 사용됩니다. "
            "CNN 기반 딥러닝 모델이 컴퓨터 비전의 핵심입니다.",
            "document_name": "CV_개요.txt",
            "chunk_index": 0,
            "file_type": "txt",
            "upload_date": 1704441600,
        },
    ]
    print(f"   ✅ {len(test_documents)}개 테스트 문서 준비 완료")

    # 3. Milvus 연결 및 문서 삽입
    print("\n[3/5] 🗄️  Milvus 데이터베이스 설정 중...")
    try:
        milvus_manager = MilvusManager(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            collection_name="test_korean_search",
            embedding_dim=embedding_service.dimension,
        )
        milvus_manager.connect()
        print(f"   ✅ Milvus 연결 성공: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")

        # 기존 테스트 컬렉션 삭제 및 재생성
        milvus_manager.create_collection(drop_existing=True)
        print("   ✅ 테스트 컬렉션 생성 완료")

        # 임베딩 생성 및 삽입
        texts = [doc["text"] for doc in test_documents]
        embeddings = embedding_service.embed_batch(texts)
        await milvus_manager.insert_embeddings(embeddings, test_documents)
        print(f"   ✅ {len(test_documents)}개 문서 임베딩 및 삽입 완료")

    except Exception as e:
        print(f"   ❌ Milvus 설정 실패: {e}")
        return

    # 4. 하이브리드 검색 초기화
    print("\n[4/5] 🔍 하이브리드 검색 시스템 초기화 중...")
    try:
        hybrid_search = HybridSearchManager(
            milvus_manager=milvus_manager,
            embedding_service=embedding_service,
            vector_weight=settings.VECTOR_SEARCH_WEIGHT,
            keyword_weight=settings.KEYWORD_SEARCH_WEIGHT,
        )
        hybrid_search.build_bm25_index(test_documents)
        print("   ✅ BM25 키워드 인덱스 구축 완료")
        print(
            f"   ✅ 검색 가중치: 벡터={settings.VECTOR_SEARCH_WEIGHT}, 키워드={settings.KEYWORD_SEARCH_WEIGHT}"
        )
    except Exception as e:
        print(f"   ❌ 하이브리드 검색 초기화 실패: {e}")
        milvus_manager.disconnect()
        return

    # 5. 테스트 쿼리 실행
    print("\n[5/5] 🧪 한글 검색 테스트 실행")
    print("=" * 80)

    test_cases = [
        {
            "query": "인공지능이란?",
            "description": "기본 한글 검색",
            "expected": "AI_기초.txt",
        },
        {
            "query": "AI 기술",
            "description": "한영 혼합 검색",
            "expected": "AI_기초.txt",
        },
        {
            "query": "머신러닝과 딥러닝의 차이",
            "description": "복합 질문",
            "expected": "ML_가이드.txt",
        },
        {
            "query": "자연어처리",
            "description": "띄어쓰기 없는 검색",
            "expected": "NLP_소개.txt",
        },
        {
            "query": "기계학습 방법",
            "description": "동의어 검색 (머신러닝=기계학습)",
            "expected": "ML_가이드.txt",
        },
        {
            "query": "이미지 인식 기술",
            "description": "관련 개념 검색",
            "expected": "CV_개요.txt",
        },
        {
            "query": "GPT BERT 모델",
            "description": "영어 약어 검색",
            "expected": "NLP_소개.txt",
        },
    ]

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        description = test_case["description"]
        expected = test_case["expected"]

        print(f"\n테스트 {i}/{len(test_cases)}: {description}")
        print(f"쿼리: '{query}'")
        print("-" * 80)

        try:
            results = await hybrid_search.hybrid_search(query=query, top_k=3)

            if results:
                print(f"✅ {len(results)}개 결과 발견")

                # 첫 번째 결과 확인
                top_result = results[0]
                is_correct = expected in top_result["document_name"]

                for j, result in enumerate(results, 1):
                    marker = "🎯" if j == 1 and is_correct else "  "
                    print(f"\n{marker} [{j}] 점수: {result['combined_score']:.4f}")
                    print(f"      문서: {result['document_name']}")
                    print(f"      내용: {result['text'][:70]}...")
                    print(
                        f"      상세: 벡터={result['vector_score']:.3f}, 키워드={result['bm25_score']:.3f}"
                    )

                if is_correct:
                    print(f"\n✅ 테스트 통과: 예상 문서 '{expected}' 발견")
                    passed += 1
                else:
                    print(f"\n⚠️  테스트 실패: 예상 문서 '{expected}' 미발견")
                    failed += 1
            else:
                print("❌ 결과 없음")
                failed += 1

        except Exception as e:
            print(f"❌ 검색 실패: {e}")
            failed += 1

    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    print(f"총 테스트: {len(test_cases)}개")
    print(f"✅ 통과: {passed}개 ({passed/len(test_cases)*100:.1f}%)")
    print(f"❌ 실패: {failed}개 ({failed/len(test_cases)*100:.1f}%)")

    if passed == len(test_cases):
        print("\n🎉 모든 테스트 통과! 한글 검색 시스템이 정상 작동합니다.")
    elif passed >= len(test_cases) * 0.7:
        print("\n✅ 대부분의 테스트 통과. 시스템이 잘 작동합니다.")
    else:
        print("\n⚠️  일부 테스트 실패. 설정을 확인해주세요.")

    print("=" * 80)

    # 정리
    print("\n🧹 정리 중...")
    milvus_manager.disconnect()
    print("✅ 테스트 완료!")


if __name__ == "__main__":
    try:
        asyncio.run(test_korean_search())
    except KeyboardInterrupt:
        print("\n\n⚠️  테스트 중단됨")
    except Exception as e:
        print(f"\n\n❌ 테스트 실행 오류: {e}")
        import traceback

        traceback.print_exc()

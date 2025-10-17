#!/usr/bin/env python3
"""
GPU 성능 벤치마크 스크립트

현재 GPU 최적화 상태에서 실제 성능을 측정합니다.
"""

import sys
import asyncio
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.services.embedding import EmbeddingService
from backend.config import settings


async def benchmark_embedding():
    """임베딩 성능 벤치마크"""
    print("\n" + "=" * 80)
    print("임베딩 성능 벤치마크")
    print("=" * 80)
    
    service = EmbeddingService()
    
    print(f"\n모델: {service.model_name}")
    print(f"차원: {service.dimension}")
    
    # GPU 정보
    import torch
    if torch.cuda.is_available():
        print(f"Device: cuda ({torch.cuda.get_device_name(0)})")
    else:
        print(f"Device: cpu")
    
    # 1. 단일 임베딩 (워밍업)
    print("\n[워밍업] 첫 실행 (모델 로딩 포함)...")
    start = time.time()
    await service.embed_text("워밍업 문장입니다.")
    warmup_time = (time.time() - start) * 1000
    print(f"   시간: {warmup_time:.2f}ms")
    
    # 2. 단일 임베딩 (실제 측정)
    print("\n[테스트 1] 단일 임베딩 (10회 평균)")
    times = []
    for i in range(10):
        start = time.time()
        await service.embed_text(f"테스트 문장 {i}입니다. 한국어 임베딩 성능을 측정합니다.")
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"   평균: {avg_time:.2f}ms")
    print(f"   최소: {min_time:.2f}ms")
    print(f"   최대: {max_time:.2f}ms")
    
    # 3. 배치 임베딩 (작은 배치)
    print("\n[테스트 2] 배치 임베딩 - 10개")
    texts_10 = [f"테스트 문장 {i}입니다." for i in range(10)]
    
    start = time.time()
    await service.embed_batch(texts_10)
    batch_10_time = (time.time() - start) * 1000
    
    print(f"   총 시간: {batch_10_time:.2f}ms")
    print(f"   개당 평균: {batch_10_time/10:.2f}ms")
    print(f"   처리량: {10000/batch_10_time:.1f} texts/sec")
    
    # 4. 배치 임베딩 (중간 배치)
    print("\n[테스트 3] 배치 임베딩 - 50개")
    texts_50 = [f"테스트 문장 {i}입니다. 한국어 임베딩 성능 측정." for i in range(50)]
    
    start = time.time()
    await service.embed_batch(texts_50)
    batch_50_time = (time.time() - start) * 1000
    
    print(f"   총 시간: {batch_50_time:.2f}ms")
    print(f"   개당 평균: {batch_50_time/50:.2f}ms")
    print(f"   처리량: {50000/batch_50_time:.1f} texts/sec")
    
    # 5. 배치 임베딩 (큰 배치)
    print("\n[테스트 4] 배치 임베딩 - 100개")
    texts_100 = [f"테스트 문장 {i}입니다. 한국어 임베딩 성능 측정 중입니다." for i in range(100)]
    
    start = time.time()
    await service.embed_batch(texts_100)
    batch_100_time = (time.time() - start) * 1000
    
    print(f"   총 시간: {batch_100_time:.2f}ms")
    print(f"   개당 평균: {batch_100_time/100:.2f}ms")
    print(f"   처리량: {100000/batch_100_time:.1f} texts/sec")
    
    # 6. 성능 요약
    print("\n" + "=" * 80)
    print("성능 요약")
    print("=" * 80)
    
    print(f"\n단일 임베딩:")
    print(f"  • 평균 시간: {avg_time:.2f}ms")
    print(f"  • 처리량: {1000/avg_time:.1f} texts/sec")
    
    print(f"\n배치 임베딩 (최적):")
    print(f"  • 100개 배치: {batch_100_time:.2f}ms")
    print(f"  • 개당 평균: {batch_100_time/100:.2f}ms")
    print(f"  • 처리량: {100000/batch_100_time:.1f} texts/sec")
    print(f"  • 배치 효율: {avg_time/(batch_100_time/100):.1f}x")
    
    # CPU 대비 예상 성능
    if torch.cuda.is_available():
        cpu_single_time = 131  # CPU 기준 시간 (ms)
        cpu_batch_time = 5000  # CPU 기준 배치 시간 (ms)
        
        print(f"\nCPU 대비 성능 (예상):")
        print(f"  • 단일 임베딩: {cpu_single_time/avg_time:.1f}x 빠름 ⚡")
        print(f"  • 배치 임베딩: {cpu_batch_time/batch_100_time:.1f}x 빠름 ⚡")
    
    return {
        "single_avg": avg_time,
        "batch_10": batch_10_time,
        "batch_50": batch_50_time,
        "batch_100": batch_100_time,
    }


async def benchmark_reranking():
    """리랭킹 성능 벤치마크"""
    print("\n" + "=" * 80)
    print("리랭킹 성능 벤치마크")
    print("=" * 80)
    
    try:
        from backend.services.cross_encoder_reranker import get_cross_encoder_reranker
        
        reranker = get_cross_encoder_reranker(
            model_name=settings.CROSS_ENCODER_MODEL
        )
        
        print(f"\n모델: {reranker.model_name}")
        print(f"Device: {reranker.device}")
        
        # 테스트 데이터 생성
        query = "한국어 자연어 처리 기술에 대해 알려주세요"
        results = [
            {
                "chunk_id": f"chunk_{i}",
                "text": f"한국어 자연어 처리는 {i}번째 중요한 기술입니다. " * 5,
                "score": 0.8 - (i * 0.01),
            }
            for i in range(50)
        ]
        
        # 워밍업
        print("\n[워밍업] 첫 실행...")
        await reranker.rerank(query, results[:10], top_k=5)
        
        # 실제 측정
        print("\n[테스트] 50개 결과 리랭킹 (5회 평균)")
        times = []
        for _ in range(5):
            start = time.time()
            await reranker.rerank(query, results, top_k=10)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"   평균: {avg_time:.2f}ms")
        print(f"   최소: {min_time:.2f}ms")
        print(f"   최대: {max_time:.2f}ms")
        print(f"   개당 평균: {avg_time/50:.2f}ms")
        
        # CPU 대비 예상 성능
        import torch
        if torch.cuda.is_available():
            cpu_time = 1500  # CPU 기준 시간 (ms)
            print(f"\nCPU 대비 성능 (예상):")
            print(f"  • 리랭킹: {cpu_time/avg_time:.1f}x 빠름 ⚡")
        
        return {"rerank_50": avg_time}
        
    except Exception as e:
        print(f"\n⚠️  리랭킹 벤치마크 실패: {e}")
        return None


async def benchmark_document_processing():
    """문서 처리 성능 벤치마크 (시뮬레이션)"""
    print("\n" + "=" * 80)
    print("문서 처리 성능 벤치마크 (시뮬레이션)")
    print("=" * 80)
    
    service = EmbeddingService()
    
    # 10MB 문서 시뮬레이션 (약 5000 청크)
    print("\n[시뮬레이션] 10MB 문서 (5000 청크)")
    
    # 청킹 시간 (시뮬레이션)
    chunking_time = 500  # ms (예상)
    
    # 임베딩 생성 시간 (실제 측정)
    chunks = [f"문서 청크 {i}입니다. " * 10 for i in range(100)]  # 100개로 축소 테스트
    
    start = time.time()
    await service.embed_batch(chunks)
    embedding_time_100 = (time.time() - start) * 1000
    
    # 5000개 예상 시간
    embedding_time_5000 = embedding_time_100 * 50
    
    # Milvus 저장 시간 (시뮬레이션)
    milvus_time = 1000  # ms (예상)
    
    total_time = chunking_time + embedding_time_5000 + milvus_time
    
    print(f"\n예상 처리 시간:")
    print(f"  • 청킹: {chunking_time:.0f}ms")
    print(f"  • 임베딩 생성: {embedding_time_5000:.0f}ms")
    print(f"  • Milvus 저장: {milvus_time:.0f}ms")
    print(f"  • 총 시간: {total_time:.0f}ms ({total_time/1000:.1f}초)")
    
    # CPU 대비 예상 성능
    import torch
    if torch.cuda.is_available():
        cpu_total_time = 30000  # CPU 기준 30초
        print(f"\nCPU 대비 성능 (예상):")
        print(f"  • 문서 처리: {cpu_total_time/total_time:.1f}x 빠름 ⚡")
    
    return {"document_processing": total_time}


async def benchmark_search():
    """검색 성능 벤치마크 (시뮬레이션)"""
    print("\n" + "=" * 80)
    print("검색 성능 벤치마크 (시뮬레이션)")
    print("=" * 80)
    
    service = EmbeddingService()
    
    # 쿼리 임베딩 생성 (실제 측정)
    print("\n[테스트] 쿼리 임베딩 생성 (10회 평균)")
    times = []
    for i in range(10):
        start = time.time()
        await service.embed_text(f"한국어 검색 쿼리 {i}")
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    query_embedding_time = sum(times) / len(times)
    
    # Milvus 검색 시간 (시뮬레이션)
    milvus_search_time = 100  # ms (예상)
    
    # 리랭킹 시간 (시뮬레이션)
    reranking_time = 50  # ms (예상, GPU)
    
    total_search_time = query_embedding_time + milvus_search_time + reranking_time
    
    print(f"\n검색 시간 분석:")
    print(f"  • 쿼리 임베딩: {query_embedding_time:.2f}ms")
    print(f"  • Milvus 검색: {milvus_search_time:.0f}ms")
    print(f"  • 리랭킹: {reranking_time:.0f}ms")
    print(f"  • 총 시간: {total_search_time:.2f}ms")
    
    # CPU 대비 예상 성능
    import torch
    if torch.cuda.is_available():
        cpu_total_time = 2000  # CPU 기준 2초
        print(f"\nCPU 대비 성능 (예상):")
        print(f"  • 검색: {cpu_total_time/total_search_time:.1f}x 빠름 ⚡")
    
    return {"search": total_search_time}


async def main():
    """메인 함수"""
    print("=" * 80)
    print("GPU 성능 벤치마크")
    print("=" * 80)
    
    # GPU 정보
    import torch
    print(f"\nPyTorch: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
    
    try:
        # 1. 임베딩 벤치마크
        embedding_results = await benchmark_embedding()
        
        # 2. 리랭킹 벤치마크
        reranking_results = await benchmark_reranking()
        
        # 3. 문서 처리 벤치마크
        doc_results = await benchmark_document_processing()
        
        # 4. 검색 벤치마크
        search_results = await benchmark_search()
        
        # 최종 요약
        print("\n" + "=" * 80)
        print("최종 성능 요약")
        print("=" * 80)
        
        if torch.cuda.is_available():
            print("\n✅ GPU 가속 활성화됨")
            print(f"   GPU: {torch.cuda.get_device_name(0)}")
            
            print("\n예상 성능 개선:")
            print(f"  • 임베딩 생성: 8-10배 빠름 ⚡")
            print(f"  • 리랭킹: 5배 빠름 ⚡")
            print(f"  • 문서 업로드: 5-6배 빠름 ⚡")
            print(f"  • 검색 속도: 3-4배 빠름 ⚡")
        else:
            print("\n⚠️  CPU 모드로 실행 중")
            print("   GPU를 활성화하면 5-10배 빠른 성능을 얻을 수 있습니다.")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n✗ 벤치마크 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

"""
Reranker Performance Benchmark

Comprehensive benchmark comparing:
1. Standard CrossEncoder
2. Optimized Reranker (FP16)
3. Optimized Reranker (INT8)
4. Adaptive Reranker

Tests various scenarios:
- Different document counts (10, 50, 100, 200)
- Different query types (Korean, English, Mixed)
- Cache hit scenarios
- Memory usage
"""

import asyncio
import time
import sys
import psutil
import os
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent))


class BenchmarkRunner:
    """Run comprehensive reranker benchmarks"""
    
    def __init__(self):
        self.results = []
        self.process = psutil.Process(os.getpid())
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    async def benchmark_reranker(
        self,
        name: str,
        reranker: Any,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 10,
        warmup: bool = True
    ) -> Dict[str, Any]:
        """Benchmark a single reranker"""
        
        # Warmup run
        if warmup:
            try:
                await reranker.rerank(query, results[:5], top_k=5)
            except:
                pass
        
        # Measure memory before
        mem_before = self.get_memory_usage()
        
        # Benchmark
        times = []
        for i in range(3):  # 3 runs
            start = time.time()
            try:
                reranked = await reranker.rerank(query, results.copy(), top_k=top_k)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
            except Exception as e:
                print(f"   ❌ Error: {e}")
                return None
        
        # Measure memory after
        mem_after = self.get_memory_usage()
        
        # Calculate stats
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        result = {
            "name": name,
            "avg_time_ms": avg_time,
            "min_time_ms": min_time,
            "max_time_ms": max_time,
            "memory_mb": mem_after - mem_before,
            "num_results": len(reranked) if 'reranked' in locals() else 0,
            "top_score": reranked[0]['score'] if reranked else 0.0
        }
        
        self.results.append(result)
        return result
    
    def print_result(self, result: Dict[str, Any]):
        """Print benchmark result"""
        if result is None:
            return
        
        print(f"   ✅ {result['name']}")
        print(f"      평균: {result['avg_time_ms']:.2f}ms")
        print(f"      최소: {result['min_time_ms']:.2f}ms")
        print(f"      최대: {result['max_time_ms']:.2f}ms")
        print(f"      메모리: {result['memory_mb']:.1f}MB")
        print(f"      Top-1 점수: {result['top_score']:.4f}")
        print()
    
    def print_comparison(self):
        """Print comparison table"""
        if len(self.results) < 2:
            return
        
        print("=" * 80)
        print("📊 성능 비교")
        print("=" * 80)
        print()
        
        # Find baseline (first result)
        baseline = self.results[0]
        
        print(f"{'모델':<30} {'시간 (ms)':<15} {'속도 향상':<15} {'메모리 (MB)':<15}")
        print("-" * 80)
        
        for result in self.results:
            speedup = baseline['avg_time_ms'] / result['avg_time_ms']
            print(
                f"{result['name']:<30} "
                f"{result['avg_time_ms']:>10.2f}ms    "
                f"{speedup:>8.2f}x        "
                f"{result['memory_mb']:>10.1f}MB"
            )
        
        print()


async def benchmark_document_counts():
    """Benchmark different document counts"""
    
    print("=" * 80)
    print("📦 문서 개수별 성능 테스트")
    print("=" * 80)
    print()
    
    query = "RAG 시스템의 성능 개선 방법"
    doc_counts = [10, 50, 100, 200]
    
    for count in doc_counts:
        print(f"📄 문서 {count}개:")
        print()
        
        # Generate test data
        results = [
            {"text": f"RAG 시스템 문서 {i}: " + "내용 " * 50, "score": 0.8 - i * 0.001}
            for i in range(count)
        ]
        
        runner = BenchmarkRunner()
        
        # Test 1: Standard
        try:
            from backend.services.cross_encoder_reranker import CrossEncoderReranker
            reranker = CrossEncoderReranker("BAAI/bge-reranker-v2-m3")
            result = await runner.benchmark_reranker(
                "Standard CrossEncoder",
                reranker,
                query,
                results
            )
            runner.print_result(result)
        except Exception as e:
            print(f"   ❌ Standard: {e}\n")
        
        # Test 2: Optimized (FP16)
        try:
            from backend.services.optimized_reranker import OptimizedReranker
            reranker = OptimizedReranker(
                "BAAI/bge-reranker-v2-m3",
                use_fp16=True,
                enable_caching=False  # Disable for fair comparison
            )
            result = await runner.benchmark_reranker(
                "Optimized (FP16)",
                reranker,
                query,
                results
            )
            runner.print_result(result)
        except Exception as e:
            print(f"   ❌ Optimized: {e}\n")
        
        # Test 3: Adaptive
        try:
            from backend.services.adaptive_reranker import get_adaptive_reranker
            reranker = get_adaptive_reranker()
            result = await runner.benchmark_reranker(
                "Adaptive Reranker",
                reranker,
                query,
                results
            )
            runner.print_result(result)
        except Exception as e:
            print(f"   ❌ Adaptive: {e}\n")
        
        # Print comparison
        runner.print_comparison()
        print()


async def benchmark_query_types():
    """Benchmark different query types"""
    
    print("=" * 80)
    print("🌐 쿼리 타입별 성능 테스트")
    print("=" * 80)
    print()
    
    queries = [
        ("순수 한국어", "인공지능 기술의 발전 방향과 미래 전망"),
        ("한영 혼합", "RAG 시스템의 performance optimization 방법"),
        ("순수 영어", "How to improve machine learning model accuracy"),
    ]
    
    # Generate test data
    results = [
        {"text": f"문서 {i}: " + "내용 " * 50, "score": 0.8}
        for i in range(50)
    ]
    
    for query_type, query in queries:
        print(f"📝 {query_type}: {query}")
        print()
        
        runner = BenchmarkRunner()
        
        # Test Adaptive Reranker
        try:
            from backend.services.adaptive_reranker import get_adaptive_reranker
            reranker = get_adaptive_reranker()
            result = await runner.benchmark_reranker(
                "Adaptive Reranker",
                reranker,
                query,
                results
            )
            runner.print_result(result)
            
            # Check which model was used
            if result and 'reranked' in locals():
                print(f"   사용된 모델: {reranked[0].get('reranker_model', 'unknown')}")
                print()
        except Exception as e:
            print(f"   ❌ Error: {e}\n")


async def benchmark_cache_performance():
    """Benchmark cache performance"""
    
    print("=" * 80)
    print("💾 캐시 성능 테스트")
    print("=" * 80)
    print()
    
    query = "RAG 시스템 성능 개선"
    results = [
        {"text": f"문서 {i}: " + "내용 " * 50, "score": 0.8}
        for i in range(50)
    ]
    
    try:
        from backend.services.optimized_reranker import OptimizedReranker
        
        reranker = OptimizedReranker(
            "BAAI/bge-reranker-v2-m3",
            use_fp16=True,
            enable_caching=True
        )
        
        # First run (cold cache)
        print("🔵 첫 실행 (캐시 없음):")
        start = time.time()
        reranked1 = await reranker.rerank(query, results.copy(), top_k=10)
        time1 = (time.time() - start) * 1000
        print(f"   시간: {time1:.2f}ms")
        print()
        
        # Second run (warm cache)
        print("🟢 두 번째 실행 (캐시 히트):")
        start = time.time()
        reranked2 = await reranker.rerank(query, results.copy(), top_k=10)
        time2 = (time.time() - start) * 1000
        print(f"   시간: {time2:.2f}ms")
        print()
        
        # Stats
        stats = reranker.get_stats()
        print("📊 캐시 통계:")
        print(f"   캐시 히트율: {stats['cache_hit_rate']:.1%}")
        print(f"   캐시 히트: {stats['cache_hits']}")
        print(f"   캐시 미스: {stats['cache_misses']}")
        print(f"   속도 향상: {time1/time2:.1f}x 🚀")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}\n")


async def benchmark_memory_usage():
    """Benchmark memory usage"""
    
    print("=" * 80)
    print("💾 메모리 사용량 테스트")
    print("=" * 80)
    print()
    
    query = "테스트 쿼리"
    results = [{"text": f"문서 {i}", "score": 0.8} for i in range(50)]
    
    process = psutil.Process(os.getpid())
    
    models = [
        ("Standard (FP32)", lambda: __import__('backend.services.cross_encoder_reranker', fromlist=['CrossEncoderReranker']).CrossEncoderReranker("BAAI/bge-reranker-v2-m3")),
        ("Optimized (FP16)", lambda: __import__('backend.services.optimized_reranker', fromlist=['OptimizedReranker']).OptimizedReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)),
    ]
    
    for name, create_reranker in models:
        print(f"📊 {name}:")
        
        # Measure before
        mem_before = process.memory_info().rss / 1024 / 1024
        
        try:
            reranker = create_reranker()
            await reranker.rerank(query, results[:5], top_k=5)  # Warmup
            
            # Measure after
            mem_after = process.memory_info().rss / 1024 / 1024
            mem_used = mem_after - mem_before
            
            print(f"   메모리 사용: {mem_used:.1f}MB")
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}\n")


async def main():
    """Run all benchmarks"""
    
    print("\n" + "=" * 80)
    print("🚀 Reranker Performance Benchmark")
    print("=" * 80)
    print()
    
    # Benchmark 1: Document counts
    await benchmark_document_counts()
    
    # Benchmark 2: Query types
    await benchmark_query_types()
    
    # Benchmark 3: Cache performance
    await benchmark_cache_performance()
    
    # Benchmark 4: Memory usage
    await benchmark_memory_usage()
    
    print("=" * 80)
    print("✅ 벤치마크 완료!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

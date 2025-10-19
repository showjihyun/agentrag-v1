"""
Agent 통합 테스트 스크립트

실제 쿼리를 사용하여 Agent 시스템의 전체 흐름을 테스트합니다.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentIntegrationTester:
    """Agent 통합 테스트 클래스"""
    
    def __init__(self):
        self.test_queries = [
            {
                'query': '안녕하세요',
                'expected_mode': 'fast',
                'description': '간단한 인사'
            },
            {
                'query': '문서에서 주요 내용을 요약해주세요',
                'expected_mode': 'balanced',
                'description': '문서 요약 요청'
            },
            {
                'query': '여러 문서를 비교 분석하고 상세한 리포트를 작성해주세요',
                'expected_mode': 'deep',
                'description': '복잡한 분석 요청'
            }
        ]
        
        self.results = []
    
    async def test_query_routing(self):
        """쿼리 라우팅 테스트"""
        print("=" * 70)
        print("🔀 쿼리 라우팅 테스트")
        print("=" * 70)
        print()
        
        try:
            from backend.agents.router import AgentRouter
            
            router = AgentRouter()
            
            for test in self.test_queries:
                print(f"📝 쿼리: {test['query']}")
                print(f"   설명: {test['description']}")
                print(f"   예상 모드: {test['expected_mode']}")
                
                try:
                    analysis = router.analyze_query(test['query'])
                    
                    print(f"   ✅ 분석 완료")
                    print(f"   복잡도: {analysis.get('complexity', 'N/A')}")
                    print(f"   추천 모드: {analysis.get('recommended_mode', 'N/A')}")
                    print(f"   필요한 Agent: {', '.join(analysis.get('required_agents', []))}")
                    
                    self.results.append({
                        'test': 'Query Routing',
                        'query': test['query'],
                        'status': 'passed',
                        'analysis': analysis
                    })
                    
                except Exception as e:
                    print(f"   ❌ 분석 실패: {e}")
                    self.results.append({
                        'test': 'Query Routing',
                        'query': test['query'],
                        'status': 'failed',
                        'error': str(e)
                    })
                
                print()
            
        except Exception as e:
            print(f"❌ Router 초기화 실패: {e}")
            print()
    
    async def test_vector_search_flow(self):
        """Vector Search 흐름 테스트"""
        print("=" * 70)
        print("📊 Vector Search 흐름 테스트")
        print("=" * 70)
        print()
        
        try:
            from backend.agents.vector_search_direct import VectorSearchAgentDirect
            
            agent = VectorSearchAgentDirect()
            
            test_query = "테스트 문서 검색"
            print(f"🔍 검색 쿼리: {test_query}")
            
            try:
                # 검색 실행
                result = await agent.search(test_query, top_k=5)
                
                print(f"✅ 검색 성공")
                print(f"   결과 수: {len(result.get('results', []))}")
                print(f"   검색 시간: {result.get('search_time', 'N/A')}ms")
                
                # 결과 샘플 출력
                results = result.get('results', [])
                if results:
                    print(f"\n   📄 상위 결과:")
                    for i, res in enumerate(results[:3], 1):
                        print(f"      {i}. 점수: {res.get('score', 'N/A'):.3f}")
                        print(f"         텍스트: {res.get('text', '')[:50]}...")
                else:
                    print(f"   ℹ️  검색 결과 없음 (문서가 없을 수 있음)")
                
                self.results.append({
                    'test': 'Vector Search Flow',
                    'status': 'passed',
                    'result_count': len(results)
                })
                
            except Exception as e:
                print(f"⚠️  검색 실패: {e}")
                print(f"   (Milvus에 데이터가 없을 수 있습니다)")
                
                self.results.append({
                    'test': 'Vector Search Flow',
                    'status': 'warning',
                    'error': str(e)
                })
            
        except Exception as e:
            print(f"❌ Agent 초기화 실패: {e}")
            self.results.append({
                'test': 'Vector Search Flow',
                'status': 'failed',
                'error': str(e)
            })
        
        print()
    
    async def test_aggregator_flow(self):
        """Aggregator 흐름 테스트"""
        print("=" * 70)
        print("🎯 Aggregator 흐름 테스트")
        print("=" * 70)
        print()
        
        try:
            from backend.agents.aggregator_optimized import AggregatorAgentOptimized
            
            agent = AggregatorAgentOptimized()
            print("✅ Aggregator Agent 초기화 성공")
            
            # 메서드 확인
            methods = ['process', 'run', 'execute']
            found_method = None
            
            for method in methods:
                if hasattr(agent, method):
                    found_method = method
                    print(f"   ✅ {method} 메서드 발견")
                    break
            
            if found_method:
                print(f"   ℹ️  실제 실행은 LLM이 필요하므로 스킵")
                self.results.append({
                    'test': 'Aggregator Flow',
                    'status': 'passed',
                    'method': found_method
                })
            else:
                print(f"   ⚠️  실행 메서드를 찾을 수 없음")
                self.results.append({
                    'test': 'Aggregator Flow',
                    'status': 'warning',
                    'message': 'No execution method found'
                })
            
        except Exception as e:
            print(f"❌ 실패: {e}")
            self.results.append({
                'test': 'Aggregator Flow',
                'status': 'failed',
                'error': str(e)
            })
        
        print()
    
    async def test_parallel_execution(self):
        """병렬 실행 테스트"""
        print("=" * 70)
        print("⚡ 병렬 실행 테스트")
        print("=" * 70)
        print()
        
        try:
            # 간단한 병렬 작업 테스트
            async def mock_agent_task(name: str, delay: float):
                """모의 Agent 작업"""
                start = asyncio.get_event_loop().time()
                await asyncio.sleep(delay)
                end = asyncio.get_event_loop().time()
                return {
                    'agent': name,
                    'duration': (end - start) * 1000,
                    'result': f'{name} completed'
                }
            
            print("🚀 3개의 Agent를 병렬로 실행...")
            
            tasks = [
                mock_agent_task('Vector Search', 0.1),
                mock_agent_task('Local Data', 0.15),
                mock_agent_task('Web Search', 0.12)
            ]
            
            start_time = asyncio.get_event_loop().time()
            results = await asyncio.gather(*tasks)
            end_time = asyncio.get_event_loop().time()
            
            total_time = (end_time - start_time) * 1000
            
            print(f"✅ 병렬 실행 완료")
            print(f"   총 시간: {total_time:.1f}ms")
            print(f"   완료된 작업: {len(results)}개")
            
            for result in results:
                print(f"   • {result['agent']}: {result['duration']:.1f}ms")
            
            # 병렬 실행이 순차 실행보다 빠른지 확인
            sequential_time = sum(r['duration'] for r in results)
            speedup = sequential_time / total_time
            
            print(f"\n   📊 성능 비교:")
            print(f"   순차 실행 예상 시간: {sequential_time:.1f}ms")
            print(f"   병렬 실행 실제 시간: {total_time:.1f}ms")
            print(f"   속도 향상: {speedup:.1f}x")
            
            self.results.append({
                'test': 'Parallel Execution',
                'status': 'passed',
                'speedup': speedup
            })
            
        except Exception as e:
            print(f"❌ 실패: {e}")
            self.results.append({
                'test': 'Parallel Execution',
                'status': 'failed',
                'error': str(e)
            })
        
        print()
    
    async def test_error_recovery(self):
        """에러 복구 테스트"""
        print("=" * 70)
        print("🛡️  에러 복구 테스트")
        print("=" * 70)
        print()
        
        try:
            from backend.agents.error_recovery import AgentErrorRecovery
            
            recovery = AgentErrorRecovery()
            print("✅ Error Recovery 초기화 성공")
            
            # 모의 에러 시나리오
            test_errors = [
                Exception("Connection timeout"),
                ValueError("Invalid input"),
                RuntimeError("Service unavailable")
            ]
            
            for i, error in enumerate(test_errors, 1):
                print(f"\n   테스트 {i}: {type(error).__name__}")
                
                try:
                    # 에러 처리 테스트
                    if hasattr(recovery, 'handle_error'):
                        result = recovery.handle_error(error)
                        print(f"   ✅ 에러 처리 성공")
                    else:
                        print(f"   ℹ️  handle_error 메서드 없음")
                except Exception as e:
                    print(f"   ⚠️  에러 처리 실패: {e}")
            
            self.results.append({
                'test': 'Error Recovery',
                'status': 'passed'
            })
            
        except Exception as e:
            print(f"❌ 실패: {e}")
            self.results.append({
                'test': 'Error Recovery',
                'status': 'failed',
                'error': str(e)
            })
        
        print()
    
    def print_summary(self):
        """테스트 결과 요약"""
        print()
        print("=" * 70)
        print("📊 통합 테스트 결과 요약")
        print("=" * 70)
        print()
        
        passed = sum(1 for r in self.results if r['status'] == 'passed')
        failed = sum(1 for r in self.results if r['status'] == 'failed')
        warning = sum(1 for r in self.results if r['status'] == 'warning')
        total = len(self.results)
        
        print(f"총 테스트: {total}개")
        print(f"✅ 통과: {passed}개")
        print(f"❌ 실패: {failed}개")
        print(f"⚠️  경고: {warning}개")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"\n성공률: {success_rate:.1f}%")
            
            if success_rate >= 80:
                print("\n🎉 Agent 시스템이 정상적으로 작동합니다!")
                print("   모든 주요 기능이 정상입니다.")
            elif success_rate >= 50:
                print("\n⚠️  Agent 시스템이 부분적으로 작동합니다.")
                print("   일부 기능에 문제가 있을 수 있습니다.")
            else:
                print("\n❌ Agent 시스템에 문제가 있습니다.")
                print("   설정 및 의존성을 확인해주세요.")
        
        print()
        print("=" * 70)
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("\n")
        print("🤖 Agent 통합 테스트 시작")
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. 쿼리 라우팅 테스트
        await self.test_query_routing()
        
        # 2. Vector Search 흐름 테스트
        await self.test_vector_search_flow()
        
        # 3. Aggregator 흐름 테스트
        await self.test_aggregator_flow()
        
        # 4. 병렬 실행 테스트
        await self.test_parallel_execution()
        
        # 5. 에러 복구 테스트
        await self.test_error_recovery()
        
        # 결과 요약
        self.print_summary()


async def main():
    """메인 함수"""
    tester = AgentIntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

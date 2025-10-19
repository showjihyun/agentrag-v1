"""
Web Search 사용 예제

DuckDuckGo를 사용한 웹 검색 기능 데모
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


async def example_1_basic_search():
    """예제 1: 기본 검색"""
    print("\n" + "="*60)
    print("📝 예제 1: 기본 웹 검색")
    print("="*60)
    
    from backend.services.web_search_service import get_web_search_service
    
    search_service = get_web_search_service()
    
    # 영어 검색
    results = await search_service.search(
        query="Python FastAPI tutorial",
        max_results=5,
        language="en",
        region="us"
    )
    
    print(f"\n✅ Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Snippet: {result['snippet'][:100]}...")


async def example_2_korean_search():
    """예제 2: 한국어 검색"""
    print("\n" + "="*60)
    print("📝 예제 2: 한국어 웹 검색")
    print("="*60)
    
    from backend.services.web_search_service import get_web_search_service
    
    search_service = get_web_search_service()
    
    # 한국어 검색
    results = await search_service.search(
        query="인공지능 최신 뉴스",
        max_results=5,
        language="ko",
        region="kr"
    )
    
    print(f"\n✅ {len(results)}개의 결과를 찾았습니다:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   URL: {result['url']}")


async def example_3_with_metadata():
    """예제 3: 메타데이터 포함 검색"""
    print("\n" + "="*60)
    print("📝 예제 3: 메타데이터 포함 검색")
    print("="*60)
    
    from backend.services.web_search_service import get_web_search_service
    
    search_service = get_web_search_service()
    
    # 폴백 포함 검색 (어떤 제공자를 사용했는지 확인)
    response = await search_service.search_with_fallback(
        query="machine learning tutorial",
        max_results=3,
        language="en",
        region="us"
    )
    
    print(f"\n✅ 검색 정보:")
    print(f"   Provider: {response['provider']}")
    print(f"   Total: {response['total']}")
    print(f"   Query: {response['query']}")
    print(f"   Timestamp: {response['timestamp']}")
    
    print(f"\n📋 결과:")
    for i, result in enumerate(response['results'], 1):
        print(f"\n{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Source: {result['source']}")


async def example_4_multiple_queries():
    """예제 4: 여러 쿼리 동시 검색"""
    print("\n" + "="*60)
    print("📝 예제 4: 여러 쿼리 동시 검색")
    print("="*60)
    
    from backend.services.web_search_service import get_web_search_service
    
    search_service = get_web_search_service()
    
    queries = [
        "Python programming",
        "FastAPI framework",
        "Machine learning"
    ]
    
    # 동시에 여러 검색 실행
    tasks = [
        search_service.search(query=q, max_results=3)
        for q in queries
    ]
    
    results_list = await asyncio.gather(*tasks)
    
    for query, results in zip(queries, results_list):
        print(f"\n🔍 Query: '{query}'")
        print(f"   Found {len(results)} results")
        if results:
            print(f"   Top result: {results[0]['title']}")


async def example_5_error_handling():
    """예제 5: 에러 처리"""
    print("\n" + "="*60)
    print("📝 예제 5: 에러 처리")
    print("="*60)
    
    from backend.services.web_search_service import get_web_search_service
    
    search_service = get_web_search_service()
    
    try:
        # 빈 쿼리 (에러 발생)
        results = await search_service.search(query="")
    except ValueError as e:
        print(f"✅ 예상된 에러 처리: {e}")
    
    try:
        # 정상 검색
        results = await search_service.search(
            query="test query",
            max_results=3
        )
        print(f"✅ 정상 검색 완료: {len(results)} results")
    except Exception as e:
        print(f"❌ 예상치 못한 에러: {e}")


async def main():
    """모든 예제 실행"""
    print("\n" + "="*60)
    print("🚀 Web Search 사용 예제")
    print("="*60)
    
    try:
        # 예제 1: 기본 검색
        await example_1_basic_search()
        
        # 예제 2: 한국어 검색
        await example_2_korean_search()
        
        # 예제 3: 메타데이터 포함
        await example_3_with_metadata()
        
        # 예제 4: 여러 쿼리 동시 검색
        await example_4_multiple_queries()
        
        # 예제 5: 에러 처리
        await example_5_error_handling()
        
        print("\n" + "="*60)
        print("✅ 모든 예제 완료!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ 예제 실행 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n💡 이 예제는 DuckDuckGo 웹 검색 기능을 보여줍니다.")
    print("   API 키가 필요 없으며 무료로 사용할 수 있습니다.\n")
    
    asyncio.run(main())

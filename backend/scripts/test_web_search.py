"""
Web Search Service 테스트 스크립트

DuckDuckGo를 사용한 웹 검색 기능 테스트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.web_search_service import get_web_search_service


async def test_basic_search():
    """기본 검색 테스트"""
    print("\n" + "="*60)
    print("🔍 기본 검색 테스트")
    print("="*60)
    
    search_service = get_web_search_service()
    
    # 테스트 쿼리
    queries = [
        "Python FastAPI tutorial",
        "인공지능 최신 뉴스",
        "LangChain documentation"
    ]
    
    for query in queries:
        print(f"\n📝 Query: '{query}'")
        print("-" * 60)
        
        try:
            results = await search_service.search(
                query=query,
                max_results=5,
                language="ko",
                region="kr"
            )
            
            if results:
                print(f"✅ Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. {result['title']}")
                    print(f"   URL: {result['url']}")
                    print(f"   Snippet: {result['snippet'][:100]}...")
                    print(f"   Source: {result['source']}")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def test_search_with_fallback():
    """폴백 포함 검색 테스트"""
    print("\n" + "="*60)
    print("🔄 폴백 포함 검색 테스트")
    print("="*60)
    
    search_service = get_web_search_service()
    
    query = "RAG system architecture"
    print(f"\n📝 Query: '{query}'")
    print("-" * 60)
    
    try:
        response = await search_service.search_with_fallback(
            query=query,
            max_results=5,
            language="en",
            region="us"
        )
        
        print(f"\n✅ Provider used: {response['provider']}")
        print(f"   Total results: {response['total']}")
        print(f"   Timestamp: {response['timestamp']}")
        
        if response.get('error'):
            print(f"   ⚠️  Error: {response['error']}")
        
        if response['results']:
            print(f"\n📋 Results:")
            for i, result in enumerate(response['results'], 1):
                print(f"\n{i}. {result['title']}")
                print(f"   URL: {result['url']}")
                print(f"   Snippet: {result['snippet'][:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_korean_search():
    """한국어 검색 테스트"""
    print("\n" + "="*60)
    print("🇰🇷 한국어 검색 테스트")
    print("="*60)
    
    search_service = get_web_search_service()
    
    queries = [
        "파이썬 프로그래밍",
        "머신러닝 튜토리얼",
        "FastAPI 사용법"
    ]
    
    for query in queries:
        print(f"\n📝 Query: '{query}'")
        print("-" * 60)
        
        try:
            results = await search_service.search(
                query=query,
                max_results=3,
                language="ko",
                region="kr"
            )
            
            if results:
                print(f"✅ Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. {result['title']}")
                    print(f"   URL: {result['url']}")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def test_service_health():
    """서비스 상태 확인"""
    print("\n" + "="*60)
    print("🏥 서비스 상태 확인")
    print("="*60)
    
    search_service = get_web_search_service()
    
    print(f"\n✅ Available providers: {[p.value for p in search_service.available_providers]}")
    print(f"   Priority: {[p.value for p in search_service.provider_priority]}")
    print(f"   Timeout: {search_service.timeout}s")


async def main():
    """메인 테스트 실행"""
    print("\n" + "="*60)
    print("🚀 Web Search Service 테스트 시작")
    print("="*60)
    
    try:
        # 서비스 상태 확인
        await test_service_health()
        
        # 기본 검색 테스트
        await test_basic_search()
        
        # 폴백 포함 검색 테스트
        await test_search_with_fallback()
        
        # 한국어 검색 테스트
        await test_korean_search()
        
        print("\n" + "="*60)
        print("✅ 모든 테스트 완료!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

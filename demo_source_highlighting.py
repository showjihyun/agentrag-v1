"""
Source Highlighting Demo

실제 RAG 시스템에서 소스 하이라이팅이 어떻게 작동하는지 보여주는 데모
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.services.source_highlighter import get_source_highlighter


def print_highlighted_html(source):
    """HTML 형식으로 하이라이트된 텍스트 출력"""
    highlighter = get_source_highlighter()
    html = highlighter.format_highlighted_text(source, format_type="html")
    
    # HTML을 터미널에서 볼 수 있도록 변환
    import re
    
    # <mark> 태그를 ANSI 색상 코드로 변환
    html = re.sub(
        r'<mark[^>]*>(.*?)</mark>',
        r'\033[43m\033[30m\1\033[0m',  # 노란 배경, 검은 글자
        html
    )
    
    return html


async def demo_basic_highlighting():
    """기본 하이라이팅 데모"""
    
    print("\n" + "=" * 80)
    print("📝 Demo 1: 기본 하이라이팅")
    print("=" * 80 + "\n")
    
    # 시뮬레이션된 RAG 답변
    answer = """
    RAG 시스템은 검색 증강 생성 기술입니다.
    벡터 데이터베이스를 사용하여 관련 문서를 검색하고,
    LLM을 통해 자연스러운 답변을 생성합니다.
    """
    
    # 시뮬레이션된 소스 문서
    sources = [
        {
            "document_id": "doc1",
            "document_name": "RAG_소개.pdf",
            "text": "RAG(Retrieval-Augmented Generation)는 검색 증강 생성 기술로, 대규모 언어 모델의 한계를 극복하기 위해 외부 지식을 활용합니다. 벡터 데이터베이스를 사용하여 관련 문서를 빠르게 검색하고, 이를 컨텍스트로 제공하여 더 정확한 답변을 생성합니다.",
            "score": 0.95
        },
        {
            "document_id": "doc2",
            "document_name": "벡터_검색.pdf",
            "text": "벡터 데이터베이스는 임베딩 벡터를 저장하고 검색하는 특수한 데이터베이스입니다. Milvus, Pinecone, Weaviate 등이 있으며, 의미적 유사도 기반으로 관련 문서를 검색할 수 있습니다.",
            "score": 0.88
        },
        {
            "document_id": "doc3",
            "document_name": "LLM_활용.pdf",
            "text": "LLM(Large Language Model)을 통해 자연스러운 답변을 생성할 수 있습니다. GPT-4, Claude, LLaMA 등 다양한 모델이 있으며, 각각의 특성에 맞게 활용할 수 있습니다.",
            "score": 0.82
        }
    ]
    
    print("🤖 RAG 답변:")
    print(answer)
    print()
    
    # 하이라이팅 적용
    highlighter = get_source_highlighter()
    highlighted = highlighter.highlight_sources(answer, sources, method="auto")
    
    # 결과 출력
    print("📚 소스 문서 (하이라이트 적용):")
    print()
    
    for i, source in enumerate(highlighted, 1):
        print(f"[{i}] {source['document_name']} (관련도: {source['score']*100:.0f}%)")
        print(f"    하이라이트: {source['highlight_count']}개")
        print()
        
        if source['highlight_count'] > 0:
            # 하이라이트된 텍스트 출력
            html = print_highlighted_html(source)
            print(f"    {html}")
            print()
            
            # 하이라이트 상세 정보
            for j, highlight in enumerate(source['highlights'], 1):
                print(f"    [{j}] {highlight['type'].upper()} 매칭")
                print(f"        구문: \"{highlight['matched_phrase'][:50]}...\"")
                print(f"        점수: {highlight['score']:.2f}")
                print()
        else:
            print(f"    {source['text'][:100]}...")
            print()
        
        print("-" * 80)
        print()


async def demo_multilingual():
    """다국어 하이라이팅 데모"""
    
    print("\n" + "=" * 80)
    print("🌐 Demo 2: 다국어 하이라이팅 (한영 혼합)")
    print("=" * 80 + "\n")
    
    answer = "RAG는 Retrieval-Augmented Generation의 약자입니다."
    
    sources = [
        {
            "document_id": "doc1",
            "text": "RAG는 Retrieval-Augmented Generation의 약자로, 검색 증강 생성을 의미합니다. 이 기술은 LLM과 벡터 검색을 결합하여 더 정확한 답변을 제공합니다.",
            "score": 0.95
        }
    ]
    
    print("🤖 답변:", answer)
    print()
    
    highlighter = get_source_highlighter()
    highlighted = highlighter.highlight_sources(answer, sources)
    
    print("📚 소스 문서:")
    print()
    
    for source in highlighted:
        html = print_highlighted_html(source)
        print(f"    {html}")
        print()


async def demo_fuzzy_matching():
    """유사 매칭 데모"""
    
    print("\n" + "=" * 80)
    print("🔍 Demo 3: 유사 매칭 (Fuzzy Matching)")
    print("=" * 80 + "\n")
    
    answer = "머신러닝 모델의 정확도를 향상시키는 방법"
    
    sources = [
        {
            "document_id": "doc1",
            "text": "기계학습 모델의 정확도를 개선하는 방법에는 여러 가지가 있습니다. 데이터 품질 향상, 하이퍼파라미터 튜닝, 앙상블 기법 등을 활용할 수 있습니다.",
            "score": 0.85
        }
    ]
    
    print("🤖 답변:", answer)
    print("📝 참고: '머신러닝'과 '기계학습', '향상'과 '개선'은 유사한 표현입니다")
    print()
    
    from backend.services.source_highlighter import SourceHighlighter
    highlighter = SourceHighlighter(fuzzy_threshold=0.6)  # 낮은 임계값
    highlighted = highlighter.highlight_sources(answer, sources, method="fuzzy")
    
    print("📚 소스 문서:")
    print()
    
    for source in highlighted:
        if source['highlight_count'] > 0:
            html = print_highlighted_html(source)
            print(f"    {html}")
            print()
            
            for highlight in source['highlights']:
                print(f"    ✨ 유사도: {highlight['score']:.2%}")
                print(f"       원본: \"{highlight['matched_phrase']}\"")
                print(f"       매칭: \"{highlight['text']}\"")
                print()


async def demo_api_response():
    """API 응답 형식 데모"""
    
    print("\n" + "=" * 80)
    print("🔌 Demo 4: API 응답 형식")
    print("=" * 80 + "\n")
    
    answer = "RAG 시스템은 검색과 생성을 결합합니다."
    
    sources = [
        {
            "document_id": "doc1",
            "document_name": "RAG_개요.pdf",
            "text": "RAG 시스템은 검색과 생성을 결합한 혁신적인 기술입니다.",
            "score": 0.95,
            "chunk_id": "chunk_1"
        }
    ]
    
    highlighter = get_source_highlighter()
    highlighted = highlighter.highlight_sources(answer, sources)
    
    # JSON 형식으로 출력
    import json
    
    response = {
        "type": "final",
        "data": {
            "content": answer,
            "sources": [
                {
                    "document_id": s["document_id"],
                    "document_name": s["document_name"],
                    "text": s["text"],
                    "score": s["score"],
                    "chunk_id": s["chunk_id"],
                    "highlights": s.get("highlights", []),
                    "highlight_count": s.get("highlight_count", 0)
                }
                for s in highlighted
            ]
        }
    }
    
    print("📤 API 응답 (JSON):")
    print()
    print(json.dumps(response, ensure_ascii=False, indent=2))
    print()


async def main():
    """모든 데모 실행"""
    
    print("\n" + "🎬" * 40)
    print("   Source Highlighting Demo")
    print("   RAG 답변의 근거를 자동으로 강조하는 기능")
    print("🎬" * 40)
    
    # Demo 1: 기본 하이라이팅
    await demo_basic_highlighting()
    
    # Demo 2: 다국어
    await demo_multilingual()
    
    # Demo 3: 유사 매칭
    await demo_fuzzy_matching()
    
    # Demo 4: API 응답
    await demo_api_response()
    
    print("\n" + "=" * 80)
    print("✅ 모든 데모 완료!")
    print("=" * 80)
    print()
    print("💡 Tip: 실제 시스템에서는 이 기능이 자동으로 적용됩니다.")
    print("   별도 설정 없이 모든 RAG 쿼리에서 소스 하이라이팅을 확인할 수 있습니다.")
    print()


if __name__ == "__main__":
    asyncio.run(main())

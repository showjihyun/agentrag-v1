"""
이미지 업로드 기능 데모 스크립트

실제 이미지를 업로드하고 쿼리하는 전체 워크플로우를 시연합니다.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


async def create_demo_images():
    """데모용 이미지 생성"""
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    print("📸 데모 이미지 생성 중...")
    
    demo_dir = Path("demo_images")
    demo_dir.mkdir(exist_ok=True)
    
    images = []
    
    # 1. 간단한 텍스트 이미지
    img1 = Image.new('RGB', (800, 400), color='white')
    draw1 = ImageDraw.Draw(img1)
    
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    text1 = """
    RAG 시스템 아키텍처
    
    1. 문서 업로드 및 처리
    2. 벡터 임베딩 생성
    3. Milvus 벡터 DB 저장
    4. 쿼리 처리 및 검색
    5. LLM 응답 생성
    """
    
    draw1.text((50, 50), text1, fill='black', font=font)
    path1 = demo_dir / "architecture.png"
    img1.save(path1)
    images.append(("아키텍처 다이어그램", path1))
    
    # 2. 데이터 차트 이미지
    img2 = Image.new('RGB', (800, 400), color='white')
    draw2 = ImageDraw.Draw(img2)
    
    text2 = """
    성능 지표 (2025년 10월)
    
    - 평균 응답 시간: 1.5초
    - 정확도: 95%
    - 처리량: 1000 req/min
    - 가용성: 99.9%
    """
    
    draw2.text((50, 50), text2, fill='black', font=font)
    path2 = demo_dir / "metrics.png"
    img2.save(path2)
    images.append(("성능 지표", path2))
    
    # 3. 코드 스크린샷
    img3 = Image.new('RGB', (800, 400), color='#1e1e1e')
    draw3 = ImageDraw.Draw(img3)
    
    text3 = """
    # Python 코드 예시
    
    async def process_query(query: str):
        # 임베딩 생성
        embedding = await embed(query)
        
        # 벡터 검색
        results = await search(embedding)
        
        # LLM 응답
        return await generate(results)
    """
    
    draw3.text((50, 50), text3, fill='#d4d4d4', font=font)
    path3 = demo_dir / "code.png"
    img3.save(path3)
    images.append(("코드 스크린샷", path3))
    
    print(f"✅ {len(images)}개의 데모 이미지 생성 완료\n")
    
    return images


async def demo_upload_and_query():
    """이미지 업로드 및 쿼리 데모"""
    print("=" * 80)
    print("🎬 이미지 업로드 기능 데모")
    print("=" * 80)
    print()
    
    # 1. 데모 이미지 생성
    images = await create_demo_images()
    
    # 2. 이미지 처리 테스트
    print("🔍 이미지 처리 테스트\n")
    
    from backend.services.image_processor import get_image_processor
    
    processor = get_image_processor(use_gpu=True, enable_vision_fallback=True)
    
    for name, path in images:
        print(f"📄 처리 중: {name}")
        print(f"   파일: {path}")
        
        try:
            result = await processor.process_image(str(path))
            
            print(f"   ✅ 성공!")
            print(f"   - 방식: {result.get('method', 'unknown')}")
            print(f"   - 신뢰도: {result.get('confidence', 'N/A')}")
            print(f"   - 텍스트 길이: {len(result.get('text', ''))} 문자")
            print(f"   - 미리보기: {result.get('text', '')[:100]}...")
            print()
            
        except Exception as e:
            print(f"   ❌ 실패: {e}")
            print()
    
    # 3. DocumentProcessor 통합 테스트
    print("📚 DocumentProcessor 통합 테스트\n")
    
    from backend.services.document_processor import DocumentProcessor
    
    doc_processor = DocumentProcessor()
    
    for name, path in images[:1]:  # 첫 번째 이미지만 테스트
        print(f"📄 처리 중: {name}")
        
        try:
            with open(path, 'rb') as f:
                content = f.read()
            
            # 텍스트 추출
            text = doc_processor.extract_text(content, 'png')
            print(f"   ✅ 텍스트 추출: {len(text)} 문자")
            
            # 청킹
            chunks = doc_processor.chunk_text(text, "demo-doc-123")
            print(f"   ✅ 청킹 완료: {len(chunks)}개 청크")
            
            # 임베딩
            from backend.services.embedding import EmbeddingService
            embedding_service = EmbeddingService()
            
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = await embedding_service.embed_batch(chunk_texts)
            print(f"   ✅ 임베딩 생성: {len(embeddings)}개 (차원: {len(embeddings[0])})")
            print()
            
        except Exception as e:
            print(f"   ❌ 실패: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    # 4. 사용 가이드
    print("=" * 80)
    print("📖 사용 가이드")
    print("=" * 80)
    print()
    print("1️⃣ 백엔드 시작:")
    print("   cd backend")
    print("   uvicorn main:app --reload --port 8000")
    print()
    print("2️⃣ 프론트엔드 시작:")
    print("   cd frontend")
    print("   npm run dev")
    print()
    print("3️⃣ 이미지 업로드:")
    print("   - 브라우저에서 http://localhost:3000 접속")
    print("   - 'Document Upload' 섹션으로 이동")
    print("   - demo_images/ 폴더의 이미지를 드래그 앤 드롭")
    print()
    print("4️⃣ 쿼리 예시:")
    print("   - 'RAG 시스템의 아키텍처를 설명해줘'")
    print("   - '성능 지표를 요약해줘'")
    print("   - '코드 예시를 보여줘'")
    print()
    print("=" * 80)
    print("✅ 데모 완료!")
    print("=" * 80)


async def quick_test():
    """빠른 기능 테스트"""
    print("\n🚀 빠른 기능 테스트\n")
    
    from PIL import Image, ImageDraw, ImageFont
    import tempfile
    import os
    
    # 테스트 이미지 생성
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw.text((20, 20), "Hello World!\n안녕하세요!", fill='black', font=font)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
        img.save(tmp.name)
        test_path = tmp.name
    
    try:
        from backend.services.image_processor import get_image_processor
        
        processor = get_image_processor(use_gpu=True, enable_vision_fallback=True)
        result = await processor.process_image(test_path)
        
        print(f"✅ 이미지 처리 성공!")
        print(f"   방식: {result.get('method')}")
        print(f"   텍스트: {result.get('text')}")
        print(f"   신뢰도: {result.get('confidence')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False
        
    finally:
        if os.path.exists(test_path):
            os.unlink(test_path)


async def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='이미지 업로드 기능 데모')
    parser.add_argument('--quick', action='store_true', help='빠른 테스트만 실행')
    args = parser.parse_args()
    
    if args.quick:
        success = await quick_test()
        sys.exit(0 if success else 1)
    else:
        await demo_upload_and_query()


if __name__ == "__main__":
    asyncio.run(main())

"""
Docling 통합 테스트 스크립트

Docling이 제대로 설치되고 작동하는지 확인
"""

import asyncio
import logging
import sys
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_docling_installation():
    """Docling 설치 확인"""
    print("\n" + "="*60)
    print("Step 1: Docling 설치 확인")
    print("="*60)
    
    try:
        import docling
        # Docling doesn't have __version__, check if it can be imported
        print(f"✅ Docling 설치됨")
        return True
    except ImportError as e:
        print(f"⚠️  Docling 설치 안됨: {e}")
        print("\n참고:")
        print("  Docling은 선택적 기능입니다")
        print("  Docling 없이도 시스템은 정상 작동합니다")
        print("  - PyPDF2로 텍스트 추출")
        print("  - ColPali로 이미지 처리")
        return False


async def test_docling_processor():
    """Docling Processor 초기화 테스트"""
    print("\n" + "="*60)
    print("Step 2: Docling Processor 초기화")
    print("="*60)
    
    try:
        from backend.services.docling_processor import get_docling_processor
        
        processor = get_docling_processor()
        stats = processor.get_stats()
        
        print(f"✅ Docling Processor 초기화 성공")
        print(f"   - Docling 사용 가능: {stats['docling_available']}")
        print(f"   - ColPali 사용 가능: {stats['colpali_available']}")
        print(f"   - OCR 활성화: {stats['enable_ocr']}")
        print(f"   - 표 구조 분석: {stats['enable_table_structure']}")
        print(f"   - 그림 추출: {stats['enable_figure_extraction']}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Docling Processor 초기화 실패: {e}")
        print("   Docling이 설치되지 않았습니다")
        print("   시스템은 Native 처리 방식을 사용합니다")
        return False


async def test_structured_data_service():
    """Structured Data Service 테스트"""
    print("\n" + "="*60)
    print("Step 3: Structured Data Service 초기화")
    print("="*60)
    
    try:
        from backend.services.structured_data_service import get_structured_data_service
        
        service = get_structured_data_service()
        
        print(f"✅ Structured Data Service 초기화 성공")
        print(f"   - Collection: {service.collection_name}")
        print(f"   - Milvus: {service.host}:{service.port}")
        
        return True
        
    except Exception as e:
        print(f"❌ Structured Data Service 초기화 실패: {e}")
        print("\nMilvus가 실행 중인지 확인하세요:")
        print("  docker ps | findstr milvus")
        import traceback
        traceback.print_exc()
        return False


async def test_hybrid_processor():
    """Hybrid Document Processor 테스트"""
    print("\n" + "="*60)
    print("Step 4: Hybrid Document Processor 초기화")
    print("="*60)
    
    try:
        from backend.services.hybrid_document_processor import get_hybrid_document_processor
        
        processor = get_hybrid_document_processor(use_docling=True)
        stats = processor.get_stats()
        
        print(f"✅ Hybrid Document Processor 초기화 성공")
        print(f"   - Docling 사용: {stats['use_docling']}")
        print(f"   - Docling 사용 가능: {stats['docling_available']}")
        print(f"   - ColPali 사용 가능: {stats['colpali_available']}")
        print(f"   - 구조화 데이터 사용 가능: {stats['structured_data_available']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Hybrid Document Processor 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_sample_document():
    """샘플 문서 처리 테스트 (선택적)"""
    print("\n" + "="*60)
    print("Step 5: 샘플 문서 처리 (선택적)")
    print("="*60)
    
    # 샘플 PDF 파일 찾기
    sample_files = [
        "test.pdf",
        "sample.pdf",
        "document.pdf",
        "../test.pdf"
    ]
    
    sample_file = None
    for file in sample_files:
        if Path(file).exists():
            sample_file = file
            break
    
    if not sample_file:
        print("⚠️  샘플 PDF 파일을 찾을 수 없습니다")
        print("   테스트를 건너뜁니다")
        print("\n샘플 파일을 테스트하려면:")
        print("  1. test.pdf 파일을 backend/ 폴더에 넣으세요")
        print("  2. 다시 이 스크립트를 실행하세요")
        return True
    
    try:
        from backend.services.docling_processor import get_docling_processor
        
        processor = get_docling_processor()
        
        print(f"📄 샘플 파일 처리 중: {sample_file}")
        
        result = await processor.process_document(
            file_path=sample_file,
            document_id="test_doc",
            user_id="test_user"
        )
        
        print(f"\n✅ 문서 처리 완료!")
        print(f"   - 텍스트 청크: {result['stats']['num_text_chunks']}")
        print(f"   - 표: {result['stats']['num_tables']}")
        print(f"   - 그림: {result['stats']['num_figures']}")
        print(f"   - 페이지: {result['stats']['num_pages']}")
        
        # 표 정보 출력
        if result['tables']:
            print(f"\n📊 추출된 표:")
            for i, table in enumerate(result['tables'][:3], 1):
                print(f"   {i}. {table.get('caption', '(캡션 없음)')}")
                print(f"      - 행: {table['metadata']['num_rows']}")
                print(f"      - 열: {table['metadata']['num_cols']}")
        
        # 그림 정보 출력
        if result['figures']:
            print(f"\n🖼️  추출된 그림:")
            for i, figure in enumerate(result['figures'][:3], 1):
                print(f"   {i}. {figure.get('caption', '(캡션 없음)')}")
                print(f"      - ColPali 처리: {figure['colpali_processed']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 문서 처리 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """메인 테스트 실행"""
    print("\n" + "="*60)
    print("🚀 Docling 통합 테스트 시작")
    print("="*60)
    
    results = []
    
    # 1. Docling 설치 확인
    results.append(await test_docling_installation())
    
    if not results[-1]:
        print("\n❌ Docling이 설치되지 않았습니다. 먼저 설치하세요:")
        print("   pip install docling")
        return
    
    # 2. Docling Processor
    results.append(await test_docling_processor())
    
    # 3. Structured Data Service
    results.append(await test_structured_data_service())
    
    # 4. Hybrid Processor
    results.append(await test_hybrid_processor())
    
    # 5. 샘플 문서 (선택적)
    results.append(await test_sample_document())
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"통과: {passed}/{total}")
    
    if passed == total:
        print("\n✅ 모든 테스트 통과!")
        print("\n다음 단계:")
        print("  1. 백엔드 시작: start-backend.bat")
        print("  2. 프론트엔드에서 PDF 업로드")
        print("  3. 문서 처리가 자동으로 진행됩니다!")
    elif passed >= 3:
        print(f"\n✅ 핵심 기능 작동 ({passed}/{total})")
        print("\n참고:")
        print("  - Docling이 없어도 시스템은 작동합니다")
        print("  - PyPDF2로 텍스트 추출")
        print("  - ColPali로 이미지 처리")
        print("\n다음 단계:")
        print("  1. 백엔드 시작: start-backend.bat")
        print("  2. 시스템 테스트")
    else:
        print(f"\n⚠️  {total - passed}개 테스트 실패")
        print("위의 오류 메시지를 확인하세요")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n테스트 중단됨")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()

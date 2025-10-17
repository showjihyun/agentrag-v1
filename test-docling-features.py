"""
Docling 이미지 및 표 처리 테스트
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_docling():
    """Docling 기능 테스트"""
    print("=" * 60)
    print("Docling 이미지 및 표 처리 테스트")
    print("=" * 60)
    print()
    
    try:
        from backend.services.docling_processor import get_docling_processor
        
        # Docling 프로세서 초기화
        print("1. Docling 프로세서 초기화...")
        processor = get_docling_processor(
            enable_ocr=True,
            enable_table_structure=True,
            enable_figure_extraction=True,
            images_scale=2.0
        )
        print("   ✅ 초기화 성공")
        print()
        
        # 통계 확인
        print("2. Docling 설정 확인...")
        stats = processor.get_stats()
        print(f"   - Docling 사용 가능: {stats['docling_available']}")
        print(f"   - ColPali 사용 가능: {stats['colpali_available']}")
        print(f"   - OCR 활성화: {stats['enable_ocr']}")
        print(f"   - 표 구조 분석: {stats['enable_table_structure']}")
        print(f"   - 그림 추출: {stats['enable_figure_extraction']}")
        print(f"   - 이미지 배율: {stats['images_scale']}x")
        print()
        
        # 테스트 파일 확인
        print("3. 테스트 파일 확인...")
        test_file = input("   테스트할 PDF 파일 경로를 입력하세요 (Enter로 건너뛰기): ").strip()
        
        if test_file and Path(test_file).exists():
            print(f"   ✅ 파일 발견: {test_file}")
            print()
            
            print("4. 문서 처리 중...")
            result = await processor.process_document(
                file_path=test_file,
                document_id="test_doc_001",
                user_id="test_user",
                metadata={"test": True}
            )
            
            print()
            print("=" * 60)
            print("처리 결과")
            print("=" * 60)
            print(f"📝 텍스트 청크: {result['stats']['num_text_chunks']}개")
            print(f"📊 추출된 표: {result['stats']['num_tables']}개")
            print(f"🖼️  추출된 이미지: {result['stats']['num_figures']}개")
            print(f"📄 페이지 수: {result['stats']['num_pages']}개")
            print()
            
            # 표 상세 정보
            if result['tables']:
                print("표 상세 정보:")
                for i, table in enumerate(result['tables'], 1):
                    print(f"  표 {i}:")
                    print(f"    - 페이지: {table['page_number']}")
                    print(f"    - 행 수: {table['metadata']['num_rows']}")
                    print(f"    - 열 수: {table['metadata']['num_cols']}")
                    if table['caption']:
                        print(f"    - 캡션: {table['caption'][:100]}...")
                    print()
            
            # 이미지 상세 정보
            if result['figures']:
                print("이미지 상세 정보:")
                for i, figure in enumerate(result['figures'], 1):
                    print(f"  이미지 {i}:")
                    print(f"    - 페이지: {figure['page_number']}")
                    print(f"    - ColPali 처리: {'✅' if figure['colpali_processed'] else '❌'}")
                    if figure['colpali_processed']:
                        print(f"    - 패치 수: {figure['colpali_patches']}")
                    if figure['caption']:
                        print(f"    - 캡션: {figure['caption'][:100]}...")
                    print()
            
            print("=" * 60)
            print("✅ 테스트 완료!")
            print("=" * 60)
            
        else:
            print("   ⚠️  테스트 파일을 건너뜁니다")
            print()
            print("=" * 60)
            print("Docling 기능 확인 완료")
            print("=" * 60)
            print()
            print("✅ Docling이 다음 기능을 지원합니다:")
            print("   - 표 자동 추출 및 구조 분석")
            print("   - 이미지/차트 추출")
            print("   - ColPali 멀티모달 검색")
            print("   - OCR (광학 문자 인식)")
            print("   - 레이아웃 분석")
            print()
            print("문서를 업로드하면 자동으로 처리됩니다!")
        
    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        print()
        print("필요한 패키지를 설치하세요:")
        print("  pip install docling")
        return False
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_docling())
    sys.exit(0 if success else 1)

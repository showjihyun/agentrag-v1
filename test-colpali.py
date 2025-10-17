"""
ColPali 초기화 테스트
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_colpali():
    """ColPali 초기화 테스트"""
    print("=" * 60)
    print("ColPali 초기화 테스트")
    print("=" * 60)
    print()
    
    try:
        print("1. ColPali 모듈 import 시도...")
        from colpali_engine.models import ColPali, ColPaliProcessor as ColPaliEngineProcessor
        print("   ✅ ColPali 모듈 import 성공")
        print()
        
        print("2. ColPali 프로세서 초기화 시도...")
        from backend.services.colpali_processor import get_colpali_processor
        
        processor = get_colpali_processor()
        
        if processor:
            print("   ✅ ColPali 프로세서 초기화 성공!")
            print()
            
            # 설정 확인
            print("3. ColPali 설정:")
            print(f"   - 모델: {processor.model_name}")
            print(f"   - GPU 사용: {processor.use_gpu}")
            print(f"   - 디바이스: {processor.device}")
            print(f"   - 바이너리화: {processor.enable_binarization}")
            print(f"   - 풀링: {processor.enable_pooling}")
            print()
            
            print("=" * 60)
            print("✅ ColPali가 정상적으로 작동합니다!")
            print("=" * 60)
            print()
            print("이제 Docling이 이미지를 처리할 때 ColPali를 사용합니다!")
            return True
        else:
            print("   ❌ ColPali 프로세서 초기화 실패")
            print()
            print("=" * 60)
            print("❌ ColPali를 사용할 수 없습니다")
            print("=" * 60)
            return False
        
    except ImportError as e:
        print(f"   ❌ Import 오류: {e}")
        print()
        print("ColPali 엔진이 설치되지 않았습니다.")
        print("설치: pip install colpali-engine")
        return False
    
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_colpali()
    sys.exit(0 if success else 1)

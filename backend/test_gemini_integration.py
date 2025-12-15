#!/usr/bin/env python3
"""
Gemini 3.0 MultiModal Integration Test
간단한 통합 테스트로 Gemini 서비스가 올바르게 작동하는지 확인
"""

import asyncio
import os
import sys
import base64
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path.parent))
sys.path.insert(0, str(backend_path))

try:
    from backend.services.multimodal.gemini_service import get_gemini_service, GEMINI_AVAILABLE
except ImportError:
    # Fallback for direct execution
    from services.multimodal.gemini_service import get_gemini_service, GEMINI_AVAILABLE

async def test_gemini_service():
    """Gemini 서비스 기본 테스트"""
    print("🚀 Gemini 3.0 MultiModal Integration Test")
    print("=" * 50)
    
    # 1. 패키지 설치 확인
    print("1. 패키지 설치 확인...")
    if not GEMINI_AVAILABLE:
        print("❌ google-generativeai 패키지가 설치되지 않았습니다.")
        print("   설치 명령: pip install google-generativeai>=0.8.0")
        return False
    print("✅ google-generativeai 패키지 설치됨")
    
    # 2. API 키 확인
    print("\n2. API 키 확인...")
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   설정 방법:")
        print("   - .env 파일에 GOOGLE_API_KEY=your_api_key_here 추가")
        print("   - 또는 export GOOGLE_API_KEY=your_api_key_here")
        print("   - API 키는 https://makersuite.google.com/app/apikey 에서 발급")
        return False
    print(f"✅ API 키 설정됨 (길이: {len(api_key)} 문자)")
    
    # 3. 서비스 초기화 테스트
    print("\n3. 서비스 초기화 테스트...")
    try:
        gemini_service = get_gemini_service()
        print("✅ Gemini 서비스 초기화 성공")
    except Exception as e:
        print(f"❌ 서비스 초기화 실패: {str(e)}")
        return False
    
    # 4. 헬스 체크
    print("\n4. 헬스 체크...")
    try:
        health_result = await gemini_service.health_check()
        if health_result['status'] == 'healthy':
            print("✅ Gemini API 연결 정상")
            print(f"   사용 가능한 모델: {health_result.get('models_available', [])}")
        else:
            print(f"❌ 헬스 체크 실패: {health_result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ 헬스 체크 중 오류: {str(e)}")
        return False
    
    # 5. 간단한 텍스트 생성 테스트
    print("\n5. 텍스트 생성 테스트...")
    try:
        # 간단한 이미지 분석 테스트 (1x1 픽셀 이미지)
        test_image = create_test_image()
        result = await gemini_service.analyze_image_with_text(
            image_data=test_image,
            prompt="이것은 테스트 이미지입니다. 간단히 '테스트 성공'이라고 응답해주세요.",
            model='gemini-1.5-flash',
            temperature=0.1,
            max_tokens=50
        )
        
        if result['success']:
            print("✅ 이미지 분석 테스트 성공")
            print(f"   응답: {result['result'][:100]}...")
            print(f"   처리 시간: {result.get('processing_time_seconds', 0):.2f}초")
            print(f"   사용 토큰: {result.get('usage', {}).get('total_tokens', 0)}")
        else:
            print(f"❌ 이미지 분석 테스트 실패: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 텍스트 생성 테스트 중 오류: {str(e)}")
        return False
    
    # 6. 모델 설정 확인
    print("\n6. 모델 설정 확인...")
    try:
        model_info = await gemini_service.get_model_capabilities('gemini-1.5-flash')
        print("✅ 모델 설정 조회 성공")
        print(f"   지원 기능: {model_info.get('capabilities', [])}")
        print(f"   최대 토큰: {model_info.get('max_tokens', 'Unknown')}")
    except Exception as e:
        print(f"❌ 모델 설정 조회 실패: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 모든 테스트 통과! Gemini 3.0 MultiModal 통합이 성공적으로 완료되었습니다.")
    print("\n다음 단계:")
    print("1. 워크플로우 빌더에서 Gemini Vision/Audio 블록 사용")
    print("2. /demo/gemini-multimodal 페이지에서 데모 체험")
    print("3. API 엔드포인트 테스트: /api/agent-builder/gemini/")
    
    return True

def create_test_image():
    """테스트용 1x1 픽셀 이미지 생성 (base64)"""
    # 1x1 픽셀 흰색 PNG 이미지 (base64 인코딩)
    tiny_png = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )
    return tiny_png

async def test_api_endpoints():
    """API 엔드포인트 테스트"""
    print("\n🔧 API 엔드포인트 테스트")
    print("-" * 30)
    
    try:
        import httpx
        
        # 로컬 서버가 실행 중인지 확인
        async with httpx.AsyncClient() as client:
            try:
                # Gemini MultiModal API 테스트
                response = await client.get("http://localhost:8000/api/agent-builder/gemini/health")
                if response.status_code == 200:
                    print("✅ Gemini MultiModal API 정상 작동")
                    health_data = response.json()
                    print(f"   상태: {health_data.get('status', 'unknown')}")
                else:
                    print(f"❌ Gemini API 오류: HTTP {response.status_code}")
                
                # Gemini Templates API 테스트
                response = await client.get("http://localhost:8000/api/agent-builder/gemini-templates/")
                if response.status_code == 200:
                    print("✅ Gemini Templates API 정상 작동")
                    templates_data = response.json()
                    print(f"   사용 가능한 템플릿: {templates_data.get('total', 0)}개")
                else:
                    print(f"❌ Templates API 오류: HTTP {response.status_code}")
                
                # Gemini Real-time API 테스트
                response = await client.get("http://localhost:8000/api/agent-builder/gemini-realtime/health")
                if response.status_code == 200:
                    print("✅ Gemini Real-time API 정상 작동")
                    realtime_data = response.json()
                    print(f"   활성 실행: {realtime_data.get('active_executions', 0)}개")
                else:
                    print(f"❌ Real-time API 오류: HTTP {response.status_code}")
                
                # 🌟 NEW: Gemini Advanced Fusion API 테스트
                response = await client.get("http://localhost:8000/api/agent-builder/gemini-fusion/health")
                if response.status_code == 200:
                    print("✅ Gemini Advanced Fusion API 정상 작동")
                    fusion_data = response.json()
                    print(f"   지원 전략: {len(fusion_data.get('available_strategies', []))}개")
                    print(f"   지원 모달리티: {', '.join(fusion_data.get('supported_modalities', []))}")
                else:
                    print(f"❌ Fusion API 오류: HTTP {response.status_code}")
                
                # Fusion 전략 목록 테스트
                response = await client.get("http://localhost:8000/api/agent-builder/gemini-fusion/strategies")
                if response.status_code == 200:
                    print("✅ Fusion 전략 API 정상 작동")
                    strategies_data = response.json()
                    print(f"   사용 가능한 전략: {len(strategies_data.get('strategies', []))}개")
                else:
                    print(f"❌ Fusion 전략 API 오류: HTTP {response.status_code}")
                
                # Fusion 예시 API 테스트
                response = await client.get("http://localhost:8000/api/agent-builder/gemini-fusion/examples")
                if response.status_code == 200:
                    print("✅ Fusion 예시 API 정상 작동")
                    examples_data = response.json()
                    print(f"   사용 예시: {examples_data.get('total', 0)}개")
                else:
                    print(f"❌ Fusion 예시 API 오류: HTTP {response.status_code}")
                
                # 🎬 NEW: Gemini Video Processing API 테스트
                response = await client.get("http://localhost:8000/api/agent-builder/gemini-video/health")
                if response.status_code == 200:
                    print("✅ Gemini Video Processing API 정상 작동")
                    video_data = response.json()
                    print(f"   지원 형식: {len(video_data.get('supported_formats', []))}개")
                    print(f"   분석 유형: {len(video_data.get('analysis_types', []))}개")
                else:
                    print(f"❌ Video API 오류: HTTP {response.status_code}")
                
                # Video 분석 유형 API 테스트
                response = await client.get("http://localhost:8000/api/agent-builder/gemini-video/analysis-types")
                if response.status_code == 200:
                    print("✅ Video 분석 유형 API 정상 작동")
                    types_data = response.json()
                    print(f"   분석 유형: {len(types_data.get('analysis_types', []))}개")
                else:
                    print(f"❌ Video 분석 유형 API 오류: HTTP {response.status_code}")
                
                # 🔄 NEW: Gemini Batch Processing API 테스트
                response = await client.get("http://localhost:8000/api/agent-builder/gemini-batch/health")
                if response.status_code == 200:
                    print("✅ Gemini Batch Processing API 정상 작동")
                    batch_data = response.json()
                    print(f"   최대 동시 작업: {batch_data.get('max_concurrent_jobs', 0)}개")
                    print(f"   사용 가능한 슬롯: {batch_data.get('available_slots', 0)}개")
                else:
                    print(f"❌ Batch API 오류: HTTP {response.status_code}")
                
                # Batch 통계 API 테스트
                response = await client.get("http://localhost:8000/api/agent-builder/gemini-batch/stats")
                if response.status_code == 200:
                    print("✅ Batch 통계 API 정상 작동")
                    stats_data = response.json()
                    print(f"   시스템 상태: {stats_data.get('system_health', {}).get('status', 'unknown')}")
                else:
                    print(f"❌ Batch 통계 API 오류: HTTP {response.status_code}")
                
                # 🧠 NEW: Gemini Auto-optimization API 테스트
                response = await client.get("http://localhost:8000/api/agent-builder/gemini-auto-optimizer/health")
                if response.status_code == 200:
                    print("✅ Gemini Auto-optimization API 정상 작동")
                    optimizer_data = response.json()
                    print(f"   최적화 엔진: {optimizer_data.get('details', {}).get('optimization_rules_loaded', False)}")
                    print(f"   AI 어드바이저: {optimizer_data.get('details', {}).get('gemini_service_available', False)}")
                else:
                    print(f"❌ Auto-optimizer API 오류: HTTP {response.status_code}")
                
                # Auto-optimizer 전략 API 테스트
                response = await client.get("http://localhost:8000/api/agent-builder/gemini-auto-optimizer/strategies")
                if response.status_code == 200:
                    print("✅ Auto-optimizer 전략 API 정상 작동")
                    strategies_data = response.json()
                    print(f"   사용 가능한 전략: {len(strategies_data.get('strategies', []))}개")
                else:
                    print(f"❌ Auto-optimizer 전략 API 오류: HTTP {response.status_code}")
                
                # Auto-optimizer 예시 API 테스트
                response = await client.get("http://localhost:8000/api/agent-builder/gemini-auto-optimizer/examples")
                if response.status_code == 200:
                    print("✅ Auto-optimizer 예시 API 정상 작동")
                    examples_data = response.json()
                    print(f"   최적화 예시: {examples_data.get('total', 0)}개")
                else:
                    print(f"❌ Auto-optimizer 예시 API 오류: HTTP {response.status_code}")
                    
            except httpx.ConnectError:
                print("⚠️  로컬 서버가 실행되지 않음 (http://localhost:8000)")
                print("   서버 시작: uvicorn main:app --reload --port 8000")
                
    except ImportError:
        print("⚠️  httpx 패키지가 설치되지 않음 (API 테스트 건너뜀)")
        print("   설치: pip install httpx")

if __name__ == "__main__":
    print("Gemini 3.0 MultiModal Integration Test")
    print("이 테스트는 Gemini 서비스가 올바르게 설정되었는지 확인합니다.\n")
    
    # 환경변수 로드
    from dotenv import load_dotenv
    load_dotenv()
    
    # 비동기 테스트 실행
    success = asyncio.run(test_gemini_service())
    
    if success:
        # API 엔드포인트 테스트
        asyncio.run(test_api_endpoints())
        
        print("\n🎯 추천 다음 단계:")
        print("1. 프론트엔드 서버 시작: cd frontend && npm run dev")
        print("2. 백엔드 서버 시작: cd backend && uvicorn main:app --reload")
        print("3. 데모 페이지 방문:")
        print("   - 기본 데모: http://localhost:3000/demo/gemini-multimodal")
        print("   - 🎬 비디오 분석: http://localhost:3000/demo/gemini-video")
        print("   - 실시간 실행: http://localhost:3000/demo/realtime-execution")
        print("   - 🌟 완전 통합 쇼케이스: http://localhost:3000/demo/gemini-showcase")
        print("4. 워크플로우 빌더에서 Gemini 블록 사용해보기:")
        print("   - Gemini Vision Block (이미지 분석)")
        print("   - Gemini Audio Block (음성 처리)")
        print("   - 🎬 Gemini Video Block (비디오 분석)")
        print("   - 🔄 Gemini Batch Block (대량 배치 처리)")
        print("   - 🌟 Gemini Fusion Block (멀티모달 융합)")
        print("   - 🧠 Gemini Auto-optimizer Block (AI 기반 자동 최적화)")
        print("5. 고급 기능 테스트:")
        print("   - 5가지 비디오 분석 유형 (comprehensive, summary, transcript, objects, scenes)")
        print("   - 배치 처리로 여러 비디오 동시 분석")
        print("   - 4가지 융합 전략 비교 (unified, parallel, sequential, hierarchical)")
        print("   - AI 기반 자동 최적화 (5가지 전략: speed_first, accuracy_first, balanced, cost_efficient, quality_premium)")
        print("   - 실시간 워크플로우 모니터링")
        print("   - 멀티모달 템플릿 활용")
        
        sys.exit(0)
    else:
        print("\n❌ 테스트 실패. 위의 오류를 해결한 후 다시 시도해주세요.")
        sys.exit(1)
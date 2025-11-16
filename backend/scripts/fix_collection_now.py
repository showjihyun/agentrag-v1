"""
즉시 실행 스크립트: 문제가 있는 컬렉션을 삭제하고 새 스키마로 재생성
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pymilvus import connections, utility
from backend.config import settings
from backend.services.milvus import MilvusManager
from backend.db.session import SessionLocal
from backend.db.models.agent_builder import Knowledgebase
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def fix_all_collections():
    """모든 knowledgebase 컬렉션을 삭제하고 새 스키마로 재생성"""
    
    print("\n" + "="*70)
    print("Milvus 컬렉션 수정 스크립트")
    print("="*70)
    print("\n⚠️  경고: 이 스크립트는 모든 Milvus 데이터를 삭제합니다!")
    print("문서를 다시 업로드해야 합니다.\n")
    
    db = SessionLocal()
    
    try:
        # Milvus 연결
        connections.connect(
            alias="fix",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        logger.info(f"✓ Milvus 연결 성공: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}\n")
        
        # 모든 knowledgebase 조회
        knowledgebases = db.query(Knowledgebase).all()
        logger.info(f"발견된 knowledgebase: {len(knowledgebases)}개\n")
        
        if not knowledgebases:
            logger.info("처리할 knowledgebase가 없습니다.")
            return
        
        # 각 컬렉션 처리
        for i, kb in enumerate(knowledgebases, 1):
            print(f"\n[{i}/{len(knowledgebases)}] 처리 중: {kb.name}")
            print(f"  - ID: {kb.id}")
            print(f"  - Collection: {kb.milvus_collection_name}")
            
            try:
                # 1. 기존 컬렉션 삭제
                if utility.has_collection(kb.milvus_collection_name, using="fix"):
                    old_collection = utility.get_collection_stats(kb.milvus_collection_name, using="fix")
                    entity_count = old_collection.get('row_count', 0)
                    print(f"  - 기존 데이터: {entity_count}개 엔티티")
                    
                    utility.drop_collection(kb.milvus_collection_name, using="fix")
                    print(f"  ✓ 기존 컬렉션 삭제 완료")
                else:
                    print(f"  - 기존 컬렉션 없음")
                
                # 2. 새 컬렉션 생성 (knowledgebase_id 포함)
                milvus_manager = MilvusManager(
                    collection_name=kb.milvus_collection_name,
                    embedding_dim=384
                )
                milvus_manager.connect()
                milvus_manager.create_collection()
                milvus_manager.disconnect()
                
                print(f"  ✓ 새 컬렉션 생성 완료 (knowledgebase_id 필드 포함)")
                
            except Exception as e:
                print(f"  ✗ 오류 발생: {e}")
                continue
        
        print("\n" + "="*70)
        print("✓ 모든 컬렉션 수정 완료!")
        print("="*70)
        print("\n다음 단계:")
        print("1. 백엔드 서버 재시작")
        print("2. UI에서 각 knowledgebase에 문서 다시 업로드")
        print("3. 검색 기능 테스트\n")
        
    except Exception as e:
        logger.error(f"\n✗ 오류 발생: {e}", exc_info=True)
        return 1
        
    finally:
        try:
            connections.disconnect(alias="fix")
        except:
            pass
        db.close()
    
    return 0


if __name__ == "__main__":
    exit_code = fix_all_collections()
    sys.exit(exit_code)

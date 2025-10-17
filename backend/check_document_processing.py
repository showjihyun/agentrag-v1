"""
문서 처리 상태 확인 스크립트

업로드된 문서가 ColPali로 처리되었는지 확인합니다.
"""

import asyncio
import sys
import os

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)


async def check_documents():
    print("=" * 60)
    print("문서 처리 상태 확인")
    print("=" * 60)
    
    try:
        from backend.config import settings
        from backend.db.database import get_db
        from backend.db.repositories.document_repository import DocumentRepository
        from sqlalchemy.orm import Session
        
        # 데이터베이스 연결
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            doc_repo = DocumentRepository(db)
            
            # 모든 문서 조회 (guest 사용자)
            # guest 사용자 ID 가져오기
            from backend.db.repositories.user_repository import UserRepository
            user_repo = UserRepository(db)
            guest_user = user_repo.get_user_by_email("guest@localhost")
            
            if not guest_user:
                print("⚠️  guest 사용자가 없습니다.")
                print("문서를 업로드하면 자동으로 생성됩니다.")
                return
            
            documents = doc_repo.get_user_documents(user_id=guest_user.id, offset=0, limit=100)
            
            print(f"\n총 {len(documents)}개의 문서가 있습니다.\n")
            
            if len(documents) == 0:
                print("⚠️  업로드된 문서가 없습니다.")
                print("\n해결 방법:")
                print("1. 프론트엔드에서 문서 업로드")
                print("2. 또는 API로 직접 업로드:")
                print("   curl -X POST http://localhost:8000/api/documents/upload \\")
                print("     -F 'file=@your_document.pdf'")
                return
            
            # 각 문서 상태 확인
            for i, doc in enumerate(documents, 1):
                print(f"{i}. {doc.filename}")
                print(f"   ID: {doc.id}")
                print(f"   상태: {doc.status}")
                print(f"   청크 수: {doc.chunk_count}")
                print(f"   파일 크기: {doc.file_size_bytes / 1024 / 1024:.2f} MB")
                print(f"   업로드 시간: {doc.uploaded_at}")
                
                if doc.status == 'failed':
                    print(f"   ❌ 처리 실패: {doc.error_message}")
                elif doc.status == 'pending':
                    print(f"   ⏳ 처리 대기 중")
                elif doc.status == 'processing':
                    print(f"   🔄 처리 중")
                elif doc.status == 'completed':
                    print(f"   ✅ 처리 완료")
                
                # 메타데이터 확인
                if doc.extra_metadata:
                    metadata = doc.extra_metadata
                    if isinstance(metadata, str):
                        import json
                        try:
                            metadata = json.loads(metadata)
                        except:
                            pass
                    
                    if isinstance(metadata, dict):
                        processing_method = metadata.get('processing_method')
                        if processing_method:
                            print(f"   처리 방법: {processing_method}")
                            
                            if processing_method == 'colpali_only':
                                print(f"   ✅ ColPali로 처리됨 (스캔본)")
                            elif processing_method == 'hybrid':
                                print(f"   ✅ 하이브리드 처리됨 (텍스트 + ColPali)")
                            elif processing_method == 'native_only':
                                print(f"   ⚠️  텍스트만 처리됨 (ColPali 미사용)")
                        
                        text_ratio = metadata.get('text_ratio')
                        if text_ratio is not None:
                            print(f"   텍스트 비율: {text_ratio:.2f}")
                            if text_ratio < 0.3:
                                print(f"   → 스캔본으로 감지됨")
                        
                        is_scanned = metadata.get('is_scanned')
                        if is_scanned is not None:
                            print(f"   스캔본: {is_scanned}")
                        
                        colpali_processed = metadata.get('colpali_processed')
                        if colpali_processed:
                            print(f"   ✅ ColPali 처리됨")
                        
                        colpali_patches = metadata.get('colpali_patches')
                        if colpali_patches:
                            print(f"   ColPali 패치 수: {colpali_patches}")
                
                print()
            
            # ColPali 데이터 확인
            print("\n" + "=" * 60)
            print("ColPali 데이터 확인")
            print("=" * 60)
            
            from backend.services.colpali_milvus_service import get_colpali_milvus_service
            
            service = get_colpali_milvus_service()
            stats = service.get_collection_stats()
            
            print(f"\nColPali 컬렉션: {stats['name']}")
            print(f"총 패치 수: {stats['num_entities']}")
            
            if stats['num_entities'] == 0:
                print("\n⚠️  ColPali 데이터가 없습니다!")
                print("\n가능한 원인:")
                print("1. 문서가 ColPali로 처리되지 않음")
                print("   → processing_method가 'native_only'인 경우")
                print("2. 텍스트 비율이 높아서 ColPali 미사용")
                print("   → text_ratio > 0.3")
                print("\n해결 방법:")
                print("1. .env 파일 수정:")
                print("   HYBRID_COLPALI_THRESHOLD=0.5")
                print("   또는")
                print("   HYBRID_PROCESS_IMAGES_ALWAYS=True")
                print("2. 문서 재업로드")
            else:
                print(f"\n✅ {stats['num_entities']}개의 패치가 저장되어 있습니다.")
                
                # 문서별 패치 수 확인
                from pymilvus import Collection
                collection = Collection("colpali_images")
                collection.load()
                
                # 문서 ID별 그룹화
                results = collection.query(
                    expr="patch_index >= 0",
                    output_fields=["document_id", "image_id"],
                    limit=1000
                )
                
                doc_patches = {}
                for result in results:
                    doc_id = result['document_id']
                    if doc_id not in doc_patches:
                        doc_patches[doc_id] = set()
                    doc_patches[doc_id].add(result['image_id'])
                
                print(f"\n문서별 이미지 수:")
                for doc_id, images in doc_patches.items():
                    print(f"  {doc_id[:16]}...: {len(images)}개 이미지")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("확인 완료")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check_documents())

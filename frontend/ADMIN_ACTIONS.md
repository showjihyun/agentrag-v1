# Admin Actions - 시스템 관리 기능

## 개요
관리자가 시스템 데이터를 초기화하고 관리할 수 있는 기능을 추가했습니다.

## 기능

### 1. Reset Milvus DB
- **기능**: Milvus 벡터 데이터베이스의 모든 데이터 삭제
- **영향**: 모든 벡터 임베딩 삭제
- **복구**: 문서를 다시 업로드하고 처리해야 함

### 2. Delete All Files
- **기능**: 업로드된 모든 파일 삭제
- **영향**: 로컬 스토리지의 모든 문서 파일 삭제
- **복구**: 불가능 (영구 삭제)

### 3. Reset Everything
- **기능**: Milvus DB + 모든 파일 동시 삭제
- **영향**: 시스템 완전 초기화
- **복구**: 불가능

## 백엔드 API

### 엔드포인트

#### 1. POST /api/admin/reset-milvus
```json
{
  "success": true,
  "message": "Milvus database has been reset successfully",
  "collection_name": "documents"
}
```

#### 2. POST /api/admin/delete-all-files
```json
{
  "success": true,
  "message": "Deleted 15 files from 5 directories",
  "deleted_count": 15,
  "deleted_directories": ["doc1", "doc2", ...]
}
```

#### 3. POST /api/admin/reset-all
```json
{
  "success": true,
  "message": "System has been completely reset",
  "milvus": { ... },
  "files": { ... }
}
```

#### 4. GET /api/admin/stats
```json
{
  "success": true,
  "files": {
    "total_files": 15,
    "total_directories": 5
  },
  "milvus": {
    "collection_name": "documents",
    "entity_count": 1234
  }
}
```

## 프론트엔드 컴포넌트

### AdminActions.tsx

#### 위치
- 헤더 우측 상단
- SystemStatusBadge 옆

#### UI/UX

**버튼 디자인:**
- 빨간색 배경 (위험 표시)
- Database 아이콘
- "Admin" 텍스트 (데스크톱)

**드롭다운 메뉴:**
```
┌─────────────────────────┐
│ DANGER ZONE             │
├─────────────────────────┤
│ 🗄️  Reset Milvus DB     │
│ 🗑️  Delete All Files    │
├─────────────────────────┤
│ ⚠️  Reset Everything    │
└─────────────────────────┘
```

**확인 모달:**
- 중앙 모달 표시
- 경고 아이콘
- 명확한 설명
- Cancel / Confirm 버튼

**알림 토스트:**
- 우측 상단에 표시
- 성공: 초록색
- 실패: 빨간색
- 5초 후 자동 사라짐

## 보안 고려사항

### 현재 구현
- ⚠️ 인증 없음 (개발 환경)
- ⚠️ 권한 체크 없음

### 프로덕션 권장사항
```python
# backend/api/admin.py
from backend.core.auth import require_admin

@router.post("/reset-milvus")
@require_admin  # 관리자 권한 필요
async def reset_milvus(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    # ...
```

### 추가 보안 조치
1. **IP 화이트리스트**
   ```python
   ADMIN_IPS = ["127.0.0.1", "192.168.1.100"]
   
   @router.post("/reset-milvus")
   async def reset_milvus(request: Request):
       if request.client.host not in ADMIN_IPS:
           raise HTTPException(status_code=403)
   ```

2. **2단계 인증**
   - 비밀번호 재확인
   - OTP 코드 입력

3. **감사 로그**
   ```python
   logger.warning(f"Admin action: reset_milvus by {user.email} from {ip}")
   ```

## 사용 시나리오

### 1. 개발 환경 초기화
```
1. Admin 버튼 클릭
2. "Reset Everything" 선택
3. 확인 모달에서 "Confirm" 클릭
4. 시스템 완전 초기화
5. 새로운 테스트 데이터 업로드
```

### 2. Milvus 재구축
```
1. Admin 버튼 클릭
2. "Reset Milvus DB" 선택
3. 확인
4. 기존 파일은 유지되지만 벡터는 삭제됨
5. 재처리 필요
```

### 3. 스토리지 정리
```
1. Admin 버튼 클릭
2. "Delete All Files" 선택
3. 확인
4. 모든 업로드 파일 삭제
5. Milvus 데이터는 유지 (고아 데이터)
```

## 에러 처리

### 백엔드
```python
try:
    # 작업 수행
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail=str(e))
```

### 프론트엔드
```typescript
try {
  const response = await fetch(...);
  if (!response.ok) throw new Error();
  // 성공 메시지
} catch (error) {
  // 에러 메시지
}
```

## 테스트 체크리스트

### 기능 테스트
- [ ] Reset Milvus DB 정상 작동
- [ ] Delete All Files 정상 작동
- [ ] Reset Everything 정상 작동
- [ ] 확인 모달 표시
- [ ] 취소 버튼 작동
- [ ] 로딩 상태 표시
- [ ] 성공/실패 메시지 표시

### UI/UX 테스트
- [ ] 버튼 위치 적절
- [ ] 드롭다운 정상 표시
- [ ] 모달 중앙 정렬
- [ ] 토스트 알림 표시
- [ ] 다크 모드 지원
- [ ] 모바일 반응형

### 보안 테스트
- [ ] 인증 체크 (프로덕션)
- [ ] 권한 체크 (프로덕션)
- [ ] CSRF 방지
- [ ] 감사 로그 기록

## 파일 구조

```
backend/
  api/
    admin.py          # 새로 추가된 Admin API
  main.py             # admin router 추가

frontend/
  components/
    AdminActions.tsx  # 새로 추가된 Admin 버튼
  app/
    page.tsx          # AdminActions 추가
```

## 데이터베이스 영향

### Milvus
```python
# 컬렉션 삭제
pool.drop_collection(collection_name)

# 컬렉션 재생성
pool.create_collection(
    collection_name=collection_name,
    dimension=settings.EMBEDDING_DIMENSION,
)
```

### 파일 시스템
```python
# 디렉토리 삭제
shutil.rmtree(upload_dir / document_id)
```

### PostgreSQL
- 영향 없음 (메타데이터는 유지)
- 필요시 별도 API 추가 가능

## 향후 개선 계획

### 단기
- [ ] 관리자 인증 추가
- [ ] 권한 체크 구현
- [ ] 감사 로그 기록

### 중기
- [ ] 선택적 삭제 (특정 문서만)
- [ ] 백업 기능
- [ ] 복원 기능
- [ ] 스케줄링 (자동 정리)

### 장기
- [ ] 관리자 대시보드
- [ ] 상세 통계
- [ ] 작업 큐 (비동기 처리)
- [ ] 진행률 표시

## 모니터링

### 로그 확인
```bash
# 백엔드 로그
tail -f backend.log | grep "Admin action"

# Milvus 로그
docker logs milvus-standalone
```

### 메트릭
- 삭제된 파일 수
- 삭제된 벡터 수
- 작업 소요 시간
- 에러 발생 횟수

## 참고 자료

- [FastAPI HTTPException](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [React Portal](https://react.dev/reference/react-dom/createPortal)
- [Milvus Collection Management](https://milvus.io/docs/manage-collections.md)
- [Python shutil](https://docs.python.org/3/library/shutil.html)

## 결론

관리자가 시스템을 쉽게 초기화하고 관리할 수 있는 기능을 추가했습니다.

**주요 기능:**
- ✅ Milvus DB 초기화
- ✅ 업로드 파일 전체 삭제
- ✅ 시스템 완전 초기화
- ✅ 확인 모달로 안전장치
- ✅ 성공/실패 알림

**주의사항:**
- ⚠️ 프로덕션에서는 반드시 인증/권한 체크 추가
- ⚠️ 백업 기능 구현 권장
- ⚠️ 감사 로그 기록 필수

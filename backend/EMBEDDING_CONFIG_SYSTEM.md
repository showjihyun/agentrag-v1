# Embedding Configuration System

## 개요
Embedding 모델 정보를 PostgreSQL에 저장하고 동적으로 관리하는 시스템입니다.

## 아키텍처

### 데이터 흐름
```
1. 애플리케이션 시작
   └─> settings.EMBEDDING_MODEL 읽기
   └─> embedding_utils.get_embedding_dimension() 호출
   └─> PostgreSQL system_config 테이블에 저장

2. Milvus 초기화
   └─> PostgreSQL에서 embedding_dimension 조회
   └─> 해당 dimension으로 Collection 생성

3. 모델 변경 시
   └─> 새 모델 정보를 PostgreSQL에 업데이트
   └─> Milvus Collection 재생성
```

## 구성 요소

### 1. PostgreSQL 테이블
```sql
CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(50) NOT NULL DEFAULT 'string',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**저장되는 설정:**
- `embedding_model_name`: 현재 사용 중인 모델명
- `embedding_dimension`: 벡터 차원 수

### 2. embedding_utils.py
```python
def get_embedding_dimension(model_name: str) -> int:
    """모델의 dimension을 반환"""
    # 1. 알려진 모델 목록에서 조회
    # 2. 없으면 실제 모델 로드하여 확인
    # 3. 실패 시 기본값 768 반환
```

**지원 모델:**
- `jhgan/ko-sroberta-multitask`: 768
- `paraphrase-multilingual-mpnet-base-v2`: 768
- `distiluse-base-multilingual-cased-v2`: 512
- `all-MiniLM-L6-v2`: 384

### 3. SystemConfigService
```python
class SystemConfigService:
    @staticmethod
    async def get_embedding_info() -> dict:
        """현재 embedding 정보 조회"""
        
    @staticmethod
    async def update_embedding_info(model_name: str, dimension: int):
        """embedding 정보 업데이트"""
        
    @staticmethod
    async def initialize_embedding_config():
        """시작 시 embedding 설정 초기화"""
```

### 4. Admin API 통합
```python
@router.post("/reset-milvus")
async def reset_milvus():
    # PostgreSQL에서 dimension 조회
    embedding_info = await SystemConfigService.get_embedding_info()
    embedding_dim = embedding_info['dimension']
    
    # 해당 dimension으로 Collection 생성
    fields = [
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),
        # ...
    ]
```

## 설치 및 설정

### 1. 마이그레이션 실행
```bash
# 방법 1: Python 스크립트 사용
python backend/scripts/run_migration.py

# 방법 2: psql 직접 실행
psql -U postgres -d agenticrag -f backend/migrations/add_system_config_table.sql
```

### 2. 애플리케이션 시작
```bash
# 자동으로 embedding config 초기화됨
python -m uvicorn backend.main:app --reload
```

### 3. 확인
```sql
-- PostgreSQL에서 확인
SELECT * FROM system_config WHERE config_key LIKE 'embedding%';

-- 결과:
-- embedding_model_name | jhgan/ko-sroberta-multitask | string
-- embedding_dimension  | 768                         | integer
```

## 사용 예시

### 1. 현재 설정 조회
```python
from backend.services.system_config_service import SystemConfigService

# Embedding 정보 조회
info = await SystemConfigService.get_embedding_info()
print(f"Model: {info['model_name']}, Dimension: {info['dimension']}")
```

### 2. 모델 변경
```python
# 1. config.py 수정
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# 2. 애플리케이션 재시작 (자동으로 업데이트됨)
# 또는 수동 업데이트:
from backend.utils.embedding_utils import get_embedding_dimension

model_name = "sentence-transformers/all-MiniLM-L6-v2"
dimension = get_embedding_dimension(model_name)
await SystemConfigService.update_embedding_info(model_name, dimension)

# 3. Milvus 초기화
# Admin 버튼 > Reset Milvus DB
```

### 3. 새 모델 추가
```python
# embedding_utils.py에 추가
KNOWN_DIMENSIONS = {
    "jhgan/ko-sroberta-multitask": 768,
    "your-new-model": 512,  # 새 모델 추가
}
```

## API 엔드포인트

### GET /api/admin/stats
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

### POST /api/admin/reset-milvus
```json
{
  "success": true,
  "message": "Milvus database has been reset successfully",
  "collection_name": "documents"
}
```

## 장점

### 1. 동적 관리
- 하드코딩 없음
- 모델 변경 시 자동 감지
- 데이터베이스에 영구 저장

### 2. 일관성
- 모든 컴포넌트가 동일한 dimension 사용
- 중앙 집중식 관리
- 버전 관리 가능

### 3. 유연성
- 새 모델 쉽게 추가
- 런타임에 변경 가능
- 롤백 가능

### 4. 안전성
- 모델 로드 실패 시 기본값 사용
- 트랜잭션 지원
- 에러 로깅

## 모델 변경 워크플로우

### 시나리오: 한국어 모델에서 다국어 모델로 변경

```bash
# 1. config.py 수정
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# 2. 애플리케이션 재시작
uvicorn backend.main:app --reload

# 3. 로그 확인
# INFO: Initialized embedding config: paraphrase-multilingual-mpnet-base-v2 (768d)

# 4. Milvus 초기화 (Admin UI)
# - Admin 버튼 클릭
# - "Reset Milvus DB" 선택
# - 확인

# 5. 문서 재업로드
# - 기존 파일은 유지됨
# - 새 모델로 재처리 필요
```

## 트러블슈팅

### 문제 1: 마이그레이션 실패
```bash
# 해결: 수동으로 테이블 생성
psql -U postgres -d agenticrag
\i backend/migrations/add_system_config_table.sql
```

### 문제 2: Dimension 불일치
```python
# 해결: 강제 업데이트
from backend.services.system_config_service import SystemConfigService
await SystemConfigService.update_embedding_info("jhgan/ko-sroberta-multitask", 768)
```

### 문제 3: 모델 로드 실패
```python
# 해결: 알려진 모델 목록에 추가
# embedding_utils.py
KNOWN_DIMENSIONS = {
    "your-model": 768,  # 수동으로 추가
}
```

## 모니터링

### PostgreSQL 쿼리
```sql
-- 현재 설정 확인
SELECT * FROM system_config ORDER BY updated_at DESC;

-- 변경 이력 (updated_at 기준)
SELECT config_key, config_value, updated_at 
FROM system_config 
WHERE config_key LIKE 'embedding%'
ORDER BY updated_at DESC;
```

### 로그 확인
```bash
# 애플리케이션 로그
tail -f backend.log | grep -i embedding

# 출력 예시:
# INFO: Initialized embedding config: jhgan/ko-sroberta-multitask (768d)
# INFO: Creating collection with model: jhgan/ko-sroberta-multitask, dimension: 768
```

## 향후 개선 계획

### 단기
- [ ] 모델 변경 API 추가
- [ ] 변경 이력 추적
- [ ] 롤백 기능

### 중기
- [ ] 다중 모델 지원
- [ ] A/B 테스트
- [ ] 성능 비교

### 장기
- [ ] 자동 모델 선택
- [ ] 모델 앙상블
- [ ] 동적 dimension 조정

## 참고 자료

- [Sentence Transformers](https://www.sbert.net/)
- [Milvus Collection Schema](https://milvus.io/docs/schema.md)
- [PostgreSQL Triggers](https://www.postgresql.org/docs/current/triggers.html)

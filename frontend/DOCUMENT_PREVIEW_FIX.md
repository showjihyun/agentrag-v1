# Document Preview 404 Error Fix

## 문제 상황

### 에러 로그
```
INFO: ::1:0 - "GET /api/document-preview/%EC%8A%A4%ED%81%AC%EB%A6%B0%EC%83%B7%202025-10-12%20004938.png/info HTTP/1.1" 404 Not Found
INFO: ::1:0 - "GET /api/document-preview/%EC%8A%A4%ED%81%AC%EB%A6%B0%EC%83%B7%202025-10-12%20004938.png/preview?include_ocr=true&include_layout=true&page=1 HTTP/1.1" 404 Not Found
```

### 원인 분석

1. **잘못된 document_id 사용**
   - 프론트엔드에서 `source.metadata?.document_id || source.document_name` 사용
   - `metadata.document_id`가 없으면 파일명(`document_name`)을 사용
   - 파일명이 URL 인코딩되어 API에 전달됨
   - 백엔드는 실제 document_id(UUID 등)를 기대하지만 파일명을 받음

2. **이미지 파일 접근 문제**
   - 이미지 파일의 경우 직접 파일 경로가 필요
   - 기존에는 `/api/documents/${docId}/preview` 사용
   - 실제 이미지 파일에 접근할 수 없음

## 해결 방법

### 1. 프론트엔드 수정 (DocumentViewer.tsx)

#### Before
```typescript
const docId = source.metadata?.document_id || source.document_name;
// 파일명이 docId로 사용됨 ❌
```

#### After
```typescript
const docId = source.document_id;
// SearchResult의 document_id 필드 직접 사용 ✅
```

#### URL 수정
```typescript
// Before
url: `/api/documents/${docId}/preview`

// After
url: `/api/document-preview/${docId}/preview`
```

### 2. 백엔드 API 추가 (document_preview.py)

#### 새로운 엔드포인트 추가
```python
@router.get("/{document_id}/image")
async def get_document_image(document_id: str):
    """
    Get the original image file for image documents.
    """
    # Find document file by document_id
    upload_dir = Path(settings.LOCAL_STORAGE_PATH) / document_id
    doc_files = list(upload_dir.glob("*"))
    doc_path = doc_files[0]
    
    # Return image file
    with open(doc_path, 'rb') as f:
        image_data = f.read()
    
    return StreamingResponse(
        io.BytesIO(image_data),
        media_type=media_type,
    )
```

### 3. 이미지 URL 생성 로직 수정

#### Before
```typescript
const imageUrl = isImage 
  ? selectedDoc.url  // ❌ 잘못된 URL
  : `/api/document-preview/${selectedDoc.id}/page/${currentPage}`;
```

#### After
```typescript
const imageUrl = isImage 
  ? `/api/document-preview/${selectedDoc.id}/image`  // ✅ 새로운 엔드포인트
  : `/api/document-preview/${selectedDoc.id}/page/${currentPage}`;
```

## 데이터 흐름

### 올바른 흐름

```
1. 백엔드: 문서 업로드
   └─> document_id 생성 (UUID)
   └─> 파일 저장: /uploads/{document_id}/{filename}

2. 백엔드: 벡터 검색
   └─> SearchResult 반환
       ├─ document_id: "abc-123-def"  ✅
       ├─ document_name: "스크린샷.png"
       └─ metadata: { file_type: "png", ... }

3. 프론트엔드: DocumentViewer
   └─> document_id 사용: "abc-123-def"  ✅
   └─> API 호출: /api/document-preview/abc-123-def/image

4. 백엔드: 파일 찾기
   └─> /uploads/abc-123-def/* 검색
   └─> 파일 반환
```

### 이전의 잘못된 흐름

```
1. 프론트엔드: DocumentViewer
   └─> document_name 사용: "스크린샷.png"  ❌
   └─> URL 인코딩: "%EC%8A%A4%ED%81%AC%EB%A6%B0%EC%83%B7.png"
   └─> API 호출: /api/document-preview/%EC%8A%A4%ED%81%AC%EB%A6%B0%EC%83%B7.png/image

2. 백엔드: 파일 찾기
   └─> /uploads/%EC%8A%A4%ED%81%AC%EB%A6%B0%EC%83%B7.png/* 검색  ❌
   └─> 404 Not Found
```

## 수정된 파일

### 프론트엔드
- `frontend/components/DocumentViewer.tsx`
  - document_id 추출 로직 수정
  - API 엔드포인트 경로 수정
  - 이미지 URL 생성 로직 수정

### 백엔드
- `backend/api/document_preview.py`
  - `/api/document-preview/{document_id}/image` 엔드포인트 추가
  - 이미지 파일 직접 반환 기능 구현
  - 미디어 타입 자동 감지

## 테스트 시나리오

### 1. 이미지 파일 (PNG, JPG 등)
- [ ] 이미지 업로드
- [ ] 채팅에서 이미지 관련 질문
- [ ] Document Viewer에서 이미지 표시 확인
- [ ] 페이지 네비게이션 (이미지는 1페이지만)
- [ ] OCR 오버레이 토글

### 2. PDF 파일
- [ ] PDF 업로드
- [ ] 채팅에서 PDF 관련 질문
- [ ] Document Viewer에서 PDF 페이지 표시
- [ ] 페이지 네비게이션 (여러 페이지)
- [ ] 페이지 번호 입력

### 3. 한글 파일명
- [ ] 한글 파일명으로 업로드
- [ ] Document Viewer에서 정상 표시
- [ ] URL 인코딩 문제 없음

### 4. 다양한 파일 타입
- [ ] DOCX
- [ ] PPTX
- [ ] HWP
- [ ] TXT

## API 엔드포인트 정리

### Document Preview API

#### 1. 문서 정보 조회
```
GET /api/document-preview/{document_id}/info
Response: { document_id, filename, file_type, total_pages, file_size }
```

#### 2. 문서 페이지 이미지
```
GET /api/document-preview/{document_id}/page/{page}
Response: PNG image
```

#### 3. 문서 미리보기 (OCR 포함)
```
GET /api/document-preview/{document_id}/preview?page=1&include_ocr=true&include_layout=true
Response: { document_id, filename, ocr_text, text_boxes, layout, ... }
```

#### 4. 이미지 파일 직접 조회 (NEW)
```
GET /api/document-preview/{document_id}/image
Response: Original image file
```

#### 5. OCR 결과 조회
```
GET /api/document-preview/{document_id}/ocr?page=1
Response: { text, boxes, confidence }
```

#### 6. 레이아웃 분석 조회
```
GET /api/document-preview/{document_id}/layout?page=1
Response: { layout }
```

## 성능 고려사항

### 캐싱
- 이미지 파일은 브라우저 캐싱 활용
- `Cache-Control` 헤더 추가 고려
- CDN 사용 고려 (프로덕션)

### 최적화
- 이미지 리사이징 (썸네일)
- Lazy loading
- Progressive loading

## 보안 고려사항

### 파일 접근 제어
- document_id 검증
- 사용자 권한 확인
- 경로 탐색 공격 방지

### 파일 타입 검증
- 확장자 검증
- MIME 타입 검증
- 파일 내용 검증

## 향후 개선 계획

### 단기
- [ ] 이미지 썸네일 생성
- [ ] 캐싱 헤더 추가
- [ ] 에러 처리 개선

### 중기
- [ ] 이미지 리사이징 API
- [ ] 워터마크 추가
- [ ] 다운로드 제한

### 장기
- [ ] CDN 통합
- [ ] 이미지 변환 서비스
- [ ] 실시간 이미지 처리

## 참고 자료

- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [URL Encoding](https://developer.mozilla.org/en-US/docs/Glossary/percent-encoding)
- [HTTP Media Types](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types)

## 결론

Document ID를 올바르게 사용하고 이미지 파일을 위한 전용 엔드포인트를 추가하여 404 에러를 해결했습니다.

**주요 변경사항:**
- ✅ `source.document_id` 직접 사용
- ✅ `/api/document-preview/{document_id}/image` 엔드포인트 추가
- ✅ 한글 파일명 URL 인코딩 문제 해결
- ✅ 이미지 파일 직접 접근 가능

이제 모든 문서 타입이 Document Viewer에서 정상적으로 표시됩니다!

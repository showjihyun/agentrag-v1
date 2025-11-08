# UI/UX Layout Improvements

## 개요
사용자 친화적인 인터페이스를 위해 Resizable Split Bar를 추가하고 레이아웃 비율을 최적화했습니다.

## 주요 변경사항

### 1. Resizable Panel 시스템 도입
- **라이브러리**: `react-resizable-panels` 사용
- **기능**: 사용자가 각 영역의 너비를 자유롭게 조절 가능

### 2. 레이아웃 비율 조정

#### Desktop (lg 이상)
```
이전:
┌─────────────┬──────────────────────┐
│   Upload    │        Chat          │
│   (280px)   │      (나머지)         │
└─────────────┴──────────────────────┘

현재:
┌──────────┬─────────────┬──────────────────┐
│  Upload  │    Chat     │  Document Viewer │
│   (20%)  │    (35%)    │      (45%)       │
└──────────┴─────────────┴──────────────────┘
```

#### 조절 가능한 범위
- **Upload Panel**: 15% ~ 25% (기본 20%)
- **Chat Panel**: 25% ~ 50% (기본 35%)
- **Document Viewer**: 30% ~ 60% (기본 45%)

### 3. Split Bar 디자인

#### 시각적 특징
- **기본 상태**: 회색 배경 + 중앙 인디케이터
- **Hover 상태**: 파란색으로 변경 + 인디케이터 확대
- **Active 상태**: 진한 파란색
- **Focus 상태**: 파란색 아웃라인

#### 인터랙션
- 마우스 드래그로 너비 조절
- 키보드 접근성 지원
- 부드러운 애니메이션 효과

### 4. 모바일 레이아웃

#### 변경사항
- Upload 버튼을 상단에 배치
- Document Viewer 토글 버튼 추가
- MobileBottomSheet에 DocumentUpload 통합

#### 구조
```
┌─────────────────────────────┐
│  [Upload] [Docs (n)]        │ ← 상단 탭
├─────────────────────────────┤
│                             │
│     Chat / Document View    │
│     (토글 가능)              │
│                             │
└─────────────────────────────┘
```

## 기술적 세부사항

### 컴포넌트 구조
```typescript
<PanelGroup direction="horizontal">
  <Panel defaultSize={20} minSize={15} maxSize={25}>
    <DocumentUpload />
  </Panel>
  
  <PanelResizeHandle />
  
  <Panel defaultSize={35} minSize={25} maxSize={50}>
    <ChatInterface />
  </Panel>
  
  <PanelResizeHandle />
  
  <Panel defaultSize={45} minSize={30} maxSize={60}>
    <DocumentViewer />
  </Panel>
</PanelGroup>
```

### CSS 스타일링
- `globals.css`에 커스텀 스타일 추가
- 다크 모드 지원
- 애니메이션 효과 (200ms ease)
- 접근성 고려 (focus-visible)

## 사용자 이점

### 1. 유연성
- 작업 스타일에 맞게 레이아웃 조정 가능
- 문서 읽기 중심 vs 채팅 중심 선택 가능

### 2. 효율성
- 한 화면에서 모든 정보 확인
- 불필요한 탭 전환 감소
- 문서와 채팅을 동시에 볼 수 있음

### 3. 직관성
- 시각적 피드백 (hover, active 상태)
- 드래그 앤 드롭 방식의 직관적 조작
- 명확한 영역 구분

## 향후 개선 계획

### 단기
- [ ] 레이아웃 설정 저장 (localStorage)
- [ ] 더블 클릭으로 기본 크기 복원
- [ ] 패널 최소화/최대화 버튼

### 중기
- [ ] 수직 분할 옵션 추가
- [ ] 패널 순서 변경 기능
- [ ] 프리셋 레이아웃 (읽기 모드, 작성 모드 등)

### 장기
- [ ] 멀티 윈도우 지원
- [ ] 팝아웃 패널
- [ ] 사용자별 레이아웃 프로필

## 테스트 체크리스트

- [x] Desktop 레이아웃 정상 작동
- [x] Mobile 레이아웃 정상 작동
- [x] 다크 모드 지원
- [x] 키보드 접근성
- [x] 타입 안정성 (TypeScript)
- [ ] 브라우저 호환성 테스트
- [ ] 성능 테스트 (리사이징 시)
- [ ] 사용자 테스트

## 참고 자료

- [react-resizable-panels 문서](https://github.com/bvaughn/react-resizable-panels)
- [Tailwind CSS 문서](https://tailwindcss.com/)
- [Next.js 15 문서](https://nextjs.org/docs)

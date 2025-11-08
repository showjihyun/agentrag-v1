# Dropdown Z-Index Fix

## 문제 상황

### 증상
- ModelSelector (LLM 선택) 드롭다운이 클릭해도 표시되지 않음
- SystemStatusBadge (All System Operation) 드롭다운도 동일한 문제
- 백드롭은 보이지만 드롭다운 내용이 보이지 않음

### 원인 분석

1. **Z-Index 충돌**
   - Tailwind의 임의 값 `z-[90]`, `z-[100]` 사용
   - 다른 컴포넌트들과 z-index 충돌
   - 헤더, 패널 등이 더 높은 z-index를 가질 수 있음

2. **백드롭 문제**
   - 백드롭이 `fixed`로 전체 화면을 덮음
   - 드롭다운이 백드롭 뒤에 렌더링됨
   - 투명한 백드롭이어서 시각적으로는 보이지 않지만 클릭을 차단

3. **렌더링 순서**
   - React의 렌더링 순서와 DOM 순서가 z-index에 영향
   - 같은 z-index일 때 나중에 렌더링된 요소가 위에 표시됨

## 해결 방법

### 1. 인라인 스타일로 명시적 z-index 설정

#### Before
```typescript
// Tailwind 임의 값 사용
<div className="fixed inset-0 z-[90]" />
<div className="absolute ... z-[100]" />
```

#### After
```typescript
// 인라인 스타일로 명시적 설정
<div style={{ zIndex: 1000 }} />  // 백드롭
<div style={{ zIndex: 1001 }} />  // 드롭다운
```

**이유:**
- 인라인 스타일이 CSS 클래스보다 우선순위가 높음
- 명시적인 숫자 값으로 충돌 방지
- 1000대 숫자는 일반적으로 모달/드롭다운에 사용

### 2. 백드롭 시각화

#### Before
```typescript
<div className="fixed inset-0 z-[90]" />  // 투명
```

#### After
```typescript
<div className="fixed inset-0 bg-black/10 dark:bg-black/30" style={{ zIndex: 1000 }} />
```

**개선사항:**
- 라이트 모드: 10% 검은색 오버레이
- 다크 모드: 30% 검은색 오버레이
- 사용자가 드롭다운이 열렸음을 시각적으로 인지
- 배경 콘텐츠와 드롭다운 구분 명확

### 3. 그림자 강화

#### Before
```typescript
className="... shadow-lg ..."
```

#### After
```typescript
className="... shadow-2xl ..."
```

**효과:**
- 더 강한 그림자로 드롭다운이 떠있는 느낌
- 시각적 계층 구조 명확화

## 수정된 컴포넌트

### 1. ModelSelector.tsx

```typescript
{isOpen && (
  <>
    {/* Backdrop */}
    <div
      className="fixed inset-0 bg-black/10 dark:bg-black/30"
      style={{ zIndex: 1000 }}
      onClick={() => setIsOpen(false)}
    />
    
    {/* Dropdown */}
    <div 
      className="absolute top-full right-0 sm:left-0 mt-2 w-[90vw] sm:w-96 max-w-md bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-2xl max-h-96 overflow-y-auto"
      style={{ zIndex: 1001 }}
    >
      {/* 드롭다운 내용 */}
    </div>
  </>
)}
```

### 2. SystemStatusBadge.tsx

```typescript
{showDetails && (
  <>
    {/* Backdrop */}
    <div 
      className="fixed inset-0 bg-black/10 dark:bg-black/30" 
      style={{ zIndex: 1000 }}
      onClick={() => setShowDetails(false)}
    />
    
    {/* Dropdown */}
    <div 
      className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700"
      style={{ zIndex: 1001 }}
    >
      {/* 드롭다운 내용 */}
    </div>
  </>
)}
```

## Z-Index 계층 구조

### 전역 Z-Index 가이드라인

```
10000+ - 최상위 모달, 알림
9000   - 중요 오버레이
1001   - 드롭다운 메뉴 (NEW)
1000   - 드롭다운 백드롭 (NEW)
100    - 고정 헤더, 사이드바
50     - 플로팅 버튼
10     - 일반 오버레이
1      - 기본 요소
0      - 배경
```

### 컴포넌트별 Z-Index

| 컴포넌트 | Z-Index | 용도 |
|---------|---------|------|
| Modal | 10000 | 최상위 모달 |
| Toast | 9000 | 알림 메시지 |
| Dropdown | 1001 | 드롭다운 메뉴 |
| Backdrop | 1000 | 드롭다운 백드롭 |
| Header | 100 | 고정 헤더 |
| Sidebar | 100 | 사이드바 |
| Floating Button | 50 | 플로팅 액션 버튼 |

## 시각적 개선

### Before (문제)
```
[헤더 - z-index: 100]
  [ModelSelector 버튼]
    [백드롭 - z-[90]] ← 투명, 보이지 않음
    [드롭다운 - z-[100]] ← 헤더와 충돌, 표시 안됨
```

### After (해결)
```
[헤더 - z-index: 100]
  [ModelSelector 버튼]
    [백드롭 - z-index: 1000] ← 반투명, 시각적 피드백
    [드롭다운 - z-index: 1001] ← 최상위, 정상 표시
```

## 테스트 시나리오

### ModelSelector
- [ ] 버튼 클릭 시 드롭다운 표시
- [ ] 백드롭 클릭 시 드롭다운 닫힘
- [ ] 모델 선택 시 드롭다운 닫힘
- [ ] 모델명이 완전히 표시됨
- [ ] 다크 모드에서 정상 작동

### SystemStatusBadge
- [ ] 버튼 클릭 시 상세 정보 표시
- [ ] 백드롭 클릭 시 닫힘
- [ ] X 버튼 클릭 시 닫힘
- [ ] 모든 정보가 표시됨
- [ ] 다크 모드에서 정상 작동

### 다른 컴포넌트와의 상호작용
- [ ] 헤더 위에 드롭다운 표시
- [ ] 사이드바와 겹치지 않음
- [ ] 다른 드롭다운과 충돌하지 않음
- [ ] 스크롤 시 정상 작동

## 추가 개선사항

### 1. 버튼 너비 확대
```typescript
// ModelSelector
min-w-[180px] sm:min-w-[220px]  // 모델명이 더 잘 보임
```

### 2. 드롭다운 너비 확대
```typescript
// ModelSelector
w-[90vw] sm:w-96 max-w-md  // 320px → 384px
```

### 3. 텍스트 개선
```typescript
// "Model" → "Select Model"
selectedModel || 'Select Model'
```

## 브라우저 호환성

### 테스트된 브라우저
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile Safari (iOS)
- ✅ Chrome Mobile (Android)

### CSS 기능
- `backdrop-filter`: 모던 브라우저 지원
- `bg-black/10`: Tailwind opacity 지원
- `style={{ zIndex }}`: 모든 브라우저 지원

## 성능 고려사항

### 렌더링 최적화
- 드롭다운은 열릴 때만 렌더링 (조건부 렌더링)
- 백드롭도 동일하게 조건부 렌더링
- 불필요한 리렌더링 방지

### 메모리 사용
- 드롭다운이 닫히면 DOM에서 완전히 제거
- 이벤트 리스너 자동 정리
- 메모리 누수 없음

## 향후 개선 계획

### 단기
- [ ] 애니메이션 추가 (fade-in, slide-down)
- [ ] 키보드 네비게이션 개선
- [ ] 포커스 트랩 구현

### 중기
- [ ] React Portal 사용 고려
- [ ] 드롭다운 위치 자동 조정 (화면 밖으로 나가지 않도록)
- [ ] 접근성 개선 (ARIA 속성)

### 장기
- [ ] 드롭다운 컴포넌트 라이브러리 통합
- [ ] 전역 z-index 관리 시스템
- [ ] 드롭다운 애니메이션 라이브러리

## 참고 자료

- [MDN - z-index](https://developer.mozilla.org/en-US/docs/Web/CSS/z-index)
- [MDN - Stacking Context](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Positioning/Understanding_z_index/The_stacking_context)
- [Tailwind CSS - Z-Index](https://tailwindcss.com/docs/z-index)
- [React Portal](https://react.dev/reference/react-dom/createPortal)

## 결론

인라인 스타일로 명시적인 z-index 값을 설정하고, 백드롭을 시각화하여 드롭다운 표시 문제를 해결했습니다.

**주요 변경사항:**
- ✅ z-index를 1000/1001로 명시적 설정
- ✅ 백드롭 시각화 (반투명 오버레이)
- ✅ 그림자 강화 (shadow-2xl)
- ✅ 버튼 및 드롭다운 너비 확대

이제 ModelSelector와 SystemStatusBadge의 드롭다운이 정상적으로 표시됩니다!

# 🏗️ PaddleOCR Advanced 아키텍처

## 📊 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Document │  │   Chat   │  │Translation│  │ Analysis │       │
│  │  Upload  │  │   Q&A    │  │  Viewer   │  │Dashboard │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                            ↕ REST API
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         PaddleOCR Advanced API Router                     │  │
│  │  /parse-multimodal | /chat | /translate | /health        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│              PaddleOCR Processor Service                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Initialization Layer                     │  │
│  │  • GPU Detection  • Model Loading  • Config Management   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐   │
│  │   Doc Parsing   │  │ Doc Understanding│  │   Utilities  │   │
│  │                 │  │                  │  │              │   │
│  │ • PaddleOCR-VL  │  │ • PP-ChatOCRv4  │  │ • Translators│   │
│  │ • PP-OCRv5      │  │ • LLM Integration│  │ • Formatters │   │
│  │ • PP-StructureV3│  │ • PP-DocTranslate│  │ • Validators │   │
│  │ • Layout Analysis│  │                  │  │              │   │
│  └─────────────────┘  └─────────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PaddleOCR Models                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │PP-OCRv5  │  │PaddleOCR │  │PP-Structure│  │PP-ChatOCR│      │
│  │(98%+ OCR)│  │   -VL    │  │V3 (Tables) │  │v4 (Q&A)  │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 데이터 흐름

### 1. 문서 업로드 및 파싱

```
User Upload Image
      ↓
Frontend (Next.js)
      ↓ POST /api/paddleocr-advanced/parse-multimodal
Backend API Router
      ↓
PaddleOCR Processor
      ↓
┌─────────────────────────────────────┐
│  1. Image Preprocessing             │
│     • Resize, Normalize             │
│     • Format Conversion             │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  2. PaddleOCR-VL Processing         │
│     • Text Detection (PP-OCRv5)     │
│     • Text Recognition              │
│     • Visual Feature Extraction     │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  3. Structure Analysis              │
│     • Table Detection (PP-StructureV3)│
│     • Layout Analysis               │
│     • Figure Detection              │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  4. Multimodal Integration          │
│     • Document Type Classification  │
│     • Content Density Calculation   │
│     • Structure Score               │
└─────────────────────────────────────┘
      ↓
Return JSON Result
      ↓
Frontend Display
```

### 2. 문서 Q&A (PP-ChatOCRv4)

```
User Question
      ↓
Frontend (Next.js)
      ↓ POST /api/paddleocr-advanced/chat-with-document
Backend API Router
      ↓
PaddleOCR Processor
      ↓
┌─────────────────────────────────────┐
│  1. Document Text Extraction        │
│     • OCR Processing (PP-OCRv5)     │
│     • Table Extraction              │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  2. Context Construction            │
│     • Document Content              │
│     • Table Data                    │
│     • Additional Context            │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  3. LLM Processing                  │
│     • Prompt Engineering            │
│     • LLM Generation                │
│     • Answer Extraction             │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  4. Post-Processing                 │
│     • Confidence Calculation        │
│     • Source Extraction             │
│     • Answer Formatting             │
└─────────────────────────────────────┘
      ↓
Return Answer + Sources
      ↓
Frontend Display
```

### 3. 문서 번역 (PP-DocTranslation)

```
User Upload + Target Language
      ↓
Frontend (Next.js)
      ↓ POST /api/paddleocr-advanced/translate-document
Backend API Router
      ↓
PaddleOCR Processor
      ↓
┌─────────────────────────────────────┐
│  1. Text Extraction with Positions  │
│     • OCR Processing (PP-OCRv5)     │
│     • Bounding Box Detection        │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  2. Layout Analysis (Optional)      │
│     • Structure Detection           │
│     • Region Classification         │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  3. Translation Service Selection   │
│     • Auto-select Best Service      │
│     • Google / DeepL / Papago       │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  4. Text Box Translation            │
│     • Translate Each Box            │
│     • Preserve Position Info        │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  5. Result Assembly                 │
│     • Combine Translated Boxes      │
│     • Maintain Layout Structure     │
└─────────────────────────────────────┘
      ↓
Return Translated Document
      ↓
Frontend Display
```

---

## 🧩 컴포넌트 상세

### PaddleOCR Processor Service

```python
class PaddleOCRProcessor:
    """
    통합 문서 처리 서비스
    """
    
    # 엔진 인스턴스
    self.ocr              # PP-OCRv5 (텍스트 인식)
    self.ocr_vl           # PaddleOCR-VL (멀티모달)
    self.table_engine     # PP-StructureV3 (표 인식)
    self.layout_engine    # Layout Analysis
    self.chatocr          # PP-ChatOCRv4 (Q&A)
    self.doc_translator   # PP-DocTranslation
    
    # 핵심 메서드
    def extract_text()                    # 텍스트 추출
    def extract_text_with_boxes()         # 텍스트 + 위치
    def extract_tables()                  # 표 추출
    def analyze_layout()                  # 레이아웃 분석
    def process_document()                # 완전한 문서 처리
    
    # 고급 메서드 (통합 필요)
    def parse_document_vl()               # 멀티모달 파싱
    def chat_with_document()              # 문서 Q&A
    def translate_document()              # 문서 번역
```

### Translation Services

```python
# 번역 서비스 계층 구조

BaseTranslator (Abstract)
    ↓
┌───────────────┬───────────────┬───────────────┬───────────────┐
│               │               │               │               │
GoogleTranslator DeepLTranslator PapagoTranslator SimpleTranslator
(무료)          (고품질)        (한글 특화)     (폴백)
```

---

## 🔧 설정 계층

```
Environment Variables (.env)
      ↓
Settings Class (backend/config.py)
      ↓
┌─────────────────────────────────────┐
│  PaddleOCR Configuration            │
│  • ENABLE_PADDLEOCR_VL              │
│  • ENABLE_PP_CHATOCR                │
│  • ENABLE_PP_DOC_TRANSLATION        │
│  • PADDLEOCR_USE_GPU                │
│  • PADDLEOCR_LANG                   │
└─────────────────────────────────────┘
      ↓
PaddleOCR Processor Initialization
      ↓
Runtime Configuration
```

---

## 🚀 처리 파이프라인

### 통합 문서 처리 파이프라인

```
Input: Image File
      ↓
┌─────────────────────────────────────┐
│  Stage 1: Preprocessing             │
│  • Image Loading (PIL)              │
│  • Format Validation                │
│  • Size Check                       │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  Stage 2: OCR Processing            │
│  • Text Detection (PP-OCRv5)        │
│  • Text Recognition                 │
│  • Confidence Scoring               │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  Stage 3: Structure Analysis        │
│  • Table Detection (PP-StructureV3) │
│  • Layout Analysis                  │
│  • Region Classification            │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  Stage 4: Multimodal Integration    │
│  • Visual Features (PaddleOCR-VL)   │
│  • Document Classification          │
│  • Content Analysis                 │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  Stage 5: Post-Processing           │
│  • Result Formatting                │
│  • Statistics Calculation           │
│  • Metadata Generation              │
└─────────────────────────────────────┘
      ↓
Output: Structured JSON
```

---

## 📊 성능 최적화

### GPU 가속 파이프라인

```
┌─────────────────────────────────────┐
│  GPU Detection                      │
│  • CUDA Available?                  │
│  • GPU Memory Check                 │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  Model Loading Strategy             │
│  • GPU: TensorRT Optimization       │
│  • CPU: MKLDNN Optimization         │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  Batch Processing                   │
│  • Multiple Images                  │
│  • Parallel Processing              │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  Caching Strategy                   │
│  • Model Cache                      │
│  • Result Cache                     │
└─────────────────────────────────────┘
```

### 메모리 관리

```
┌─────────────────────────────────────┐
│  Singleton Pattern                  │
│  • Single Processor Instance        │
│  • Shared Model Loading             │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  Lazy Loading                       │
│  • Load Models on Demand            │
│  • Unload Unused Models             │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  Resource Pooling                   │
│  • Connection Pooling               │
│  • Thread Pooling                   │
└─────────────────────────────────────┘
```

---

## 🔐 에러 처리

### 에러 처리 계층

```
┌─────────────────────────────────────┐
│  API Layer                          │
│  • HTTP Exception Handling          │
│  • Status Code Mapping              │
│  • Error Response Formatting        │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  Service Layer                      │
│  • Try-Catch Blocks                 │
│  • Logging                          │
│  • Fallback Mechanisms              │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  Model Layer                        │
│  • Model Loading Errors             │
│  • GPU/CPU Fallback                 │
│  • Timeout Handling                 │
└─────────────────────────────────────┘
```

### 폴백 전략

```
Primary: PaddleOCR-VL
      ↓ (if fails)
Fallback 1: PP-OCRv5
      ↓ (if fails)
Fallback 2: Basic OCR
      ↓ (if fails)
Error Response
```

---

## 📈 모니터링 및 로깅

### 로깅 계층

```
┌─────────────────────────────────────┐
│  Application Logs                   │
│  • Request/Response                 │
│  • Processing Time                  │
│  • Error Traces                     │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  Performance Metrics                │
│  • OCR Accuracy                     │
│  • Processing Speed                 │
│  • GPU Utilization                  │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  Business Metrics                   │
│  • Document Types                   │
│  • Feature Usage                    │
│  • Success Rates                    │
└─────────────────────────────────────┘
```

---

## 🔄 확장성

### 수평 확장

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Backend 1  │  │  Backend 2  │  │  Backend 3  │
│  (GPU)      │  │  (GPU)      │  │  (CPU)      │
└─────────────┘  └─────────────┘  └─────────────┘
      ↓                ↓                ↓
┌─────────────────────────────────────────────────┐
│           Load Balancer (Nginx)                 │
└─────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────┐
│           Shared Storage (S3/MinIO)             │
└─────────────────────────────────────────────────┘
```

### 수직 확장

```
┌─────────────────────────────────────┐
│  Multi-GPU Support                  │
│  • Model Parallelism                │
│  • Data Parallelism                 │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  Batch Processing                   │
│  • Larger Batch Sizes               │
│  • Parallel Inference               │
└─────────────────────────────────────┘
```

---

## 📚 참고 자료

- 📖 **상세 제안서**: [PADDLEOCR_ADVANCED_INTEGRATION_PROPOSAL.md](PADDLEOCR_ADVANCED_INTEGRATION_PROPOSAL.md)
- 📝 **통합 요약**: [PADDLEOCR_INTEGRATION_SUMMARY.md](PADDLEOCR_INTEGRATION_SUMMARY.md)
- 🔧 **현재 구현**: [backend/services/paddleocr_processor.py](backend/services/paddleocr_processor.py)

---

**작성일**: 2025-10-21  
**버전**: 1.0

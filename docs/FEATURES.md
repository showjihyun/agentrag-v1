# 🎯 Feature Highlights

## 1. Multi-Agent Architecture

### Aggregator Agent (Master Coordinator)
- **ReAct Pattern**: Reasoning + Acting for systematic problem-solving
- **Chain of Thought**: Step-by-step reasoning process
- **Dynamic Planning**: Adapts strategy based on query complexity
- **Memory Integration**: Leverages STM and LTM for context-aware responses

### Specialized Agents

#### Vector Search Agent
```python
Capabilities:
- Semantic similarity search using Milvus
- Hybrid search (vector + keyword)
- Reranking with cross-encoders
- Source citation tracking
```

#### Local Data Agent
```python
Capabilities:
- File system access
- Database queries
- Structured data retrieval
- Metadata extraction
```

#### Web Search Agent
```python
Capabilities:
- Real-time web search
- Content extraction
- Fact verification
- Source validation
```

## 2. Adaptive Query Routing

### Automatic Complexity Analysis

```python
Query Complexity Factors:
├─ Length: Number of words/sentences
├─ Structure: Question type, clauses
├─ Intent: Information vs. analysis
├─ Context: Single vs. multi-document
└─ Reasoning: Simple lookup vs. complex inference

Complexity Score: 0.0 - 1.0
├─ 0.0 - 0.35: Fast Mode
├─ 0.35 - 0.70: Balanced Mode
└─ 0.70 - 1.0: Deep Mode
```

### Mode Characteristics

| Feature | Fast | Balanced | Deep |
|---------|------|----------|------|
| Response Time | < 1s | < 3s | < 10s |
| Documents Retrieved | 5 | 10 | 15 |
| Agent Iterations | 1-2 | 3-5 | 5-10 |
| Reasoning Depth | Basic | Moderate | Comprehensive |
| Use Cases | Simple Q&A | General queries | Complex analysis |

## 3. Multimodal Document Processing

### Supported Formats

#### Text Documents
- **PDF**: PyPDF2 + opendataloader-pdf for tables
- **DOCX**: python-docx with table extraction
- **TXT/MD**: Direct text processing
- **HWP/HWPX**: Korean Hangul format support

#### Presentations
- **PPTX**: python-pptx with slide extraction
- **PPT**: Legacy format support

#### Spreadsheets
- **XLSX**: openpyxl with formula evaluation
- **XLS**: xlrd for legacy Excel
- **CSV**: pandas integration

#### Images
- **PNG, JPG, GIF, BMP, WEBP**: OCR + ColPali

### Advanced Processing Features

#### Table Extraction
```python
Features:
├─ Structure Recognition: Rows, columns, headers
├─ Cell Merging: Handles merged cells
├─ Formula Evaluation: Calculates Excel formulas
├─ Formatting Preservation: Bold, italic, colors
└─ Search Optimization: Key-value format
```

#### Image Understanding (ColPali)
```python
Capabilities:
├─ Visual Question Answering
├─ Chart/Graph Interpretation
├─ Diagram Understanding
├─ Text in Images (OCR)
└─ Multimodal Retrieval
```

#### Contextual Retrieval
```python
Enhancement:
├─ Document Context: Title, author, date
├─ Section Context: Chapter, heading hierarchy
├─ Chunk Context: Surrounding paragraphs
└─ Semantic Context: Related concepts
```

## 4. Memory Management

### Short-Term Memory (STM)

```python
Storage: Redis
Purpose: Conversation context
Scope: Session-based
TTL: 1 hour (configurable)

Features:
├─ Message History: Last 20 messages
├─ User Preferences: Language, mode
├─ Session State: Current document, filters
└─ Temporary Cache: Recent queries
```

### Long-Term Memory (LTM)

```python
Storage: Milvus
Purpose: Pattern learning
Scope: User-based
Persistence: Permanent

Features:
├─ Query Patterns: Common question types
├─ User Preferences: Preferred sources, topics
├─ Feedback Learning: Thumbs up/down
└─ Performance Metrics: Response quality
```

## 5. Multi-LLM Support

### Supported Providers

#### Local (Ollama)
```yaml
Models:
  - llama3.1 (8B, 70B)
  - mistral (7B)
  - mixtral (8x7B)
  - codellama (7B, 13B, 34B)
  - phi-2 (2.7B)

Advantages:
  - No API costs
  - Data privacy
  - Low latency
  - Offline capability
```

#### Cloud (OpenAI)
```yaml
Models:
  - gpt-4-turbo
  - gpt-4
  - gpt-3.5-turbo

Advantages:
  - High quality
  - Large context
  - Fast inference
  - Multimodal
```

#### Cloud (Anthropic)
```yaml
Models:
  - claude-3-opus
  - claude-3-sonnet
  - claude-3-haiku

Advantages:
  - Long context (200K)
  - High reasoning
  - Safety features
  - Fast responses
```

### Automatic Fallback

```python
Strategy:
1. Try primary provider
2. If timeout/error → Try fallback #1
3. If still failing → Try fallback #2
4. If all fail → Return error with details

Configuration:
LLM_PROVIDER=ollama
LLM_FALLBACK_PROVIDERS=openai,claude
```

## 6. Real-time Streaming

### Server-Sent Events (SSE)

```typescript
Stream Types:
├─ Agent Steps: Reasoning process
├─ Document Retrieval: Sources found
├─ Partial Responses: Incremental text
├─ Citations: Source references
└─ Metadata: Confidence, timing
```

### UI Features

```typescript
Real-time Updates:
├─ Typing Animation: Character-by-character
├─ Progress Indicators: Current step
├─ Source Cards: Live citation display
├─ Reasoning Tree: Agent decision flow
└─ Error Handling: Graceful degradation
```

## 7. Performance Optimization

### Caching Strategy

```python
L1 Cache (Redis):
├─ TTL: 1 hour
├─ Scope: Exact query match
├─ Hit Rate: 40-50%
└─ Latency: < 10ms

L2 Cache (Redis):
├─ TTL: 24 hours
├─ Scope: Semantic similarity
├─ Hit Rate: 20-30%
└─ Latency: < 50ms

Total Hit Rate: 60-80%
```

### Parallel Processing

```python
Parallel Execution:
├─ Initial Retrieval: Vector + Web + Local (parallel)
├─ Agent Coordination: Independent agents run concurrently
├─ Document Processing: Batch embedding generation
└─ Reranking: Parallel cross-encoder inference

Speedup: 2-3x faster than sequential
```

### Query Optimization

```python
Techniques:
├─ Query Expansion: Synonyms, related terms
├─ Query Rewriting: Clarification, simplification
├─ Hybrid Search: Vector + keyword combination
├─ Reranking: Cross-encoder for precision
└─ Result Deduplication: Remove redundant sources
```

## 8. Korean Language Optimization

### Embedding Models

```python
Primary: jhgan/ko-sroberta-multitask
├─ Dimensions: 768
├─ Training: Korean-specific corpus
├─ Performance: Best for Korean semantic search
└─ Use Case: General Korean documents

Alternative: BM-K/KoSimCSE-roberta
├─ Dimensions: 768
├─ Training: SimCSE on Korean data
├─ Performance: Excellent similarity matching
└─ Use Case: Conversational queries
```

### Reranking Models

```python
Adaptive Selection:
├─ Korean-only content → Dongjin-kr/ko-reranker
├─ Multilingual content → BAAI/bge-reranker-v2-m3
└─ Auto-detection based on language ratio

Performance:
├─ Korean Reranker: 92% accuracy on Korean
├─ Multilingual: 88% accuracy on mixed content
└─ Fallback: Cross-encoder/ms-marco-MiniLM
```

### Text Processing

```python
Features:
├─ Morpheme Analysis: Korean word segmentation
├─ Spacing Normalization: Fix OCR spacing errors
├─ Jamo Handling: Korean character decomposition
├─ Hanja Conversion: Chinese characters to Hangul
└─ Dialect Support: Regional variations
```

## 9. Security & Privacy

### Authentication

```python
Method: JWT (JSON Web Tokens)
├─ Access Token: 24 hours
├─ Refresh Token: 7 days
├─ Algorithm: HS256
└─ Secure Storage: HttpOnly cookies
```

### Authorization

```python
Levels:
├─ User: Own documents only
├─ Admin: All documents
├─ Guest: Public documents only
└─ API Key: Programmatic access
```

### Data Privacy

```python
Features:
├─ User Isolation: Separate vector collections
├─ Document Encryption: At rest and in transit
├─ Audit Logging: All access tracked
├─ GDPR Compliance: Data deletion on request
└─ Local LLM Option: No data leaves premises
```

## 10. Monitoring & Analytics

### Real-time Metrics

```python
Query Metrics:
├─ Response Time: P50, P95, P99
├─ Mode Distribution: Fast/Balanced/Deep
├─ Cache Hit Rate: L1, L2, Total
├─ Error Rate: By type and endpoint
└─ Throughput: Queries per second

System Metrics:
├─ CPU Usage: Per service
├─ Memory Usage: Per service
├─ Disk I/O: Read/write rates
├─ Network: Bandwidth usage
└─ Database: Connection pool, query time
```

### Analytics Dashboard

```python
Visualizations:
├─ Query Volume: Time series
├─ Response Time: Histogram
├─ Mode Distribution: Pie chart
├─ Cache Performance: Line chart
├─ Error Trends: Bar chart
└─ User Activity: Heatmap
```

### Auto-tuning

```python
Adaptive Thresholds:
├─ Analyze: 1000+ queries
├─ Calculate: Optimal complexity thresholds
├─ Adjust: Mode boundaries
├─ Monitor: Performance impact
└─ Iterate: Continuous improvement

Target Distribution:
├─ Fast Mode: 40-50%
├─ Balanced Mode: 30-40%
└─ Deep Mode: 20-30%
```

---

## 🎯 Use Cases

### 1. Enterprise Knowledge Base
- Internal documentation search
- Policy and procedure lookup
- Employee onboarding
- Compliance verification

### 2. Research & Academia
- Literature review
- Paper summarization
- Citation tracking
- Cross-reference analysis

### 3. Legal & Compliance
- Contract analysis
- Regulatory research
- Case law search
- Due diligence

### 4. Customer Support
- FAQ automation
- Ticket resolution
- Knowledge base search
- Product documentation

### 5. Content Creation
- Research assistance
- Fact checking
- Source citation
- Content summarization

---

**[← Back to README](../README.md)**

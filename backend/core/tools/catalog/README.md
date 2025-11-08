# Tool Catalog

sim.ai 스타일의 tool catalog 구조입니다. 모든 tools는 카테고리별로 구조화되어 있습니다.

## 구조

```
backend/core/tools/catalog/
├── __init__.py              # Catalog 메인 모듈
├── ai_tools.py              # AI/LLM tools
├── search_tools.py          # 검색 tools
├── productivity_tools.py    # 생산성 tools
├── data_tools.py            # 데이터베이스 tools
├── communication_tools.py   # 커뮤니케이션 tools
└── developer_tools.py       # 개발자 tools
```

## 카테고리

### 1. AI Tools (ai)
- OpenAI Chat (GPT-4, GPT-3.5)
- Anthropic Claude
- Google Gemini
- Mistral AI
- Cohere
- Hugging Face
- Replicate

### 2. Search Tools (search)
- Google Search
- Bing Search
- DuckDuckGo
- Tavily Search
- Serper
- Exa Search
- Wikipedia
- arXiv
- YouTube Search

### 3. Productivity Tools (productivity)
- Notion
- Google Docs
- Google Sheets
- Google Drive
- Airtable
- Trello
- Asana
- Monday.com
- ClickUp

### 4. Communication Tools (communication)
- Slack
- Discord
- Telegram
- Gmail
- Outlook
- SendGrid
- Twilio
- Zoom

### 5. Data Tools (data)
- PostgreSQL
- MySQL
- MongoDB
- Redis
- Elasticsearch
- Snowflake
- BigQuery
- Supabase
- Firebase

### 6. Developer Tools (developer)
- GitHub
- GitLab
- Bitbucket
- Jira
- Linear
- Vercel
- Netlify
- AWS
- Docker
- Kubernetes
- Stripe

## Tool 정의 형식

각 tool은 다음 형식으로 정의됩니다:

```python
{
    "id": "tool_id",                    # 고유 ID
    "name": "Tool Name",                # 표시 이름
    "description": "Tool description",  # 설명
    "category": "category_name",        # 카테고리
    "provider": "provider_name",        # 제공자
    "icon": "🔧",                       # 아이콘 (emoji)
    "requires_auth": True/False,        # 인증 필요 여부
    "auth_type": "api_key|oauth2|...",  # 인증 타입
    "config": {                         # 추가 설정 (선택)
        "models": [...],
        "max_tokens": 4096,
        ...
    }
}
```

## API 사용법

### 모든 tools 조회
```
GET /api/agent-builder/tools
```

### 카테고리별 조회
```
GET /api/agent-builder/tools?category=ai
```

### 검색
```
GET /api/agent-builder/tools?search=google
```

### 특정 tool 조회
```
GET /api/agent-builder/tools/{tool_id}
```

### 카테고리 목록
```
GET /api/agent-builder/tools/categories
```

## 새 Tool 추가하기

1. 해당 카테고리 파일 열기 (예: `ai_tools.py`)
2. 리스트에 새 tool 정의 추가
3. 필요한 경우 새 카테고리 파일 생성
4. `__init__.py`에서 import 추가

## 특징

- ✅ 60+ tools 지원
- ✅ 6개 카테고리로 구조화
- ✅ 인증 타입 명시
- ✅ 검색 기능
- ✅ 카테고리별 필터링
- ✅ 확장 가능한 구조
- ✅ sim.ai 스타일 호환

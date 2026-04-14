# A2A 프로토콜 실전형 멀티 에이전트 시스템

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         사용자 (CLI / test_client.py)                    │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │ A2A Request
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent (Port: 10010)                      │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  agent.py (Host Agent)                                              │ │
│  │  • Intent 분석 (LLM)                                                │ │
│  │  • Plan 생성                                                        │ │
│  │  • A2A Client로 Remote Agent 호출 ◄── 공식 패턴                      │ │
│  │  • 결과 통합                                                        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │ A2A Protocol
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────────┐
│  Web Research Agent   │ │ Internal RAG Agent│ │ File Management Agent │
│    (Port: 10011)      │ │   (Port: 10012)   │ │     (Port: 10013)     │
│                       │ │                   │ │                       │
│ • MCP Tavily 서버     │ │ • LangGraph 기반  │ │ • MCP GDrive 서버     │
│ • create_agent 활용   │ │ • Supabase pgvector│ │ • 파일 업/다운로드     │
│ • 웹/뉴스 검색        │ │ • 검색 + 인덱싱    │ │ • storage_ref 관리    │
└───────────────────────┘ └───────────────────┘ └───────────────────────┘
                                      │
                                      ▼
                        ┌─────────────────────────┐
                        │     Infrastructure      │
                        │  • Google Drive (MCP)   │
                        │  • Supabase pgvector    │
                        │  • Tavily Search (MCP)  │
                        └─────────────────────────┘
```

## 환경 설정

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (.env)

```
copy .env.example .env
```

```env
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
# credentials.json 파일 필요 (Google Cloud Console에서 발급)
```

## 실행 방법

### 1단계: Web Research Agent 서버 실행

```bash
cd web_research_agent
python agent_server.py
```

서버가 `http://localhost:10011`에서 실행됩니다.

### 2단계: Internal RAG Agent 서버 실행

새로운 터미널에서:

```bash
cd internal_rag_agent
python agent_server.py
```

서버가 `http://localhost:10012`에서 실행됩니다.

### 3단계: File Management Agent 서버 실행

새로운 터미널에서:

```bash
cd file_management_agent
python agent_server.py
```

서버가 `http://localhost:10013`에서 실행됩니다.

### 4단계: Orchestrator Agent 서버 실행

새로운 터미널에서:

```bash
cd orchestrator_agent
python agent_server.py
```

서버가 `http://localhost:10010`에서 실행됩니다.

### 5단계: 클라이언트로 에이전트와 통신

새로운 터미널에서:

```bash
python test_client.py
```

## 파일 구조

```
CHAP11_final-project/
├── README.md
├── requirements.txt
├── test_client.py              # 테스트 클라이언트
├── orchestrator_agent/         # Host Agent (포트: 10010)
│   ├── agent.py
│   ├── agent_executor.py
│   └── agent_server.py
├── web_research_agent/         # Remote Agent (포트: 10011)
│   ├── agent.py
│   ├── agent_executor.py
│   └── agent_server.py
├── internal_rag_agent/         # Remote Agent (포트: 10012)
│   ├── agent.py
│   ├── agent_executor.py
│   └── agent_server.py
└── file_management_agent/      # Remote Agent (포트: 10013)
    ├── agent.py
    ├── agent_executor.py
    ├── agent_server.py
    └── gdrive_client.py
```

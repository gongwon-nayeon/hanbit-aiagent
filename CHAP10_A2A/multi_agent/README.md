# A2A 프로토콜 멀티 에이전트 예제

### 1단계: LangGraph 에이전트 서버 실행

```bash
cd CHAP10_A2A/multi_agent/langgraph_agent
python agent_server.py
```

서버가 `http://localhost:10001`에서 실행됩니다.

### 2단계: MCP 에이전트 서버 실행

새로운 터미널에서 아래와 같이 명령어를 실행합니다.

```bash
cd CHAP10_A2A/multi_agent/mcp_agent
python agent_server.py
```

서버가 `http://localhost:10002`에서 실행됩니다.

### 3단계: 오케스트레이터로 에이전트 조율

새로운 터미널에서 아래와 같이 명령어를 실행합니다.

```bash
cd CHAP10_A2A/multi_agent
python agent_orchestrator.py
```

## 파일 구조

```
multi_agent/
├── README.md
├── agent_orchestrator.py  # 멀티 에이전트 오케스트레이터
├── langgraph_agent/       # LangGraph 기반 에이전트
│   ├── agent.py
│   ├── agent_executor.py
│   └── agent_server.py
└── mcp_agent/             # MCP 기반 에이전트
    ├── agent.py
    ├── agent_executor.py
    └── agent_server.py
```

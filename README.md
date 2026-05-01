# 만들면서 배우는 AI 에이전트 개발 입문+실전 - 실습 코드

본 깃허브 레포지토리는『만들면서 배우는 AI 에이전트 개발 입문+실전』도서의 실습 코드를 담고 있습니다.

## 목차

- [파일 구성](#파일-구성)
  - [PART2 (4-5장): 랭그래프 기초](#part2-4-5장-랭그래프-기초)
  - [CHAP6_single-agent: 싱글 에이전트](#chap6_single-agent-싱글-에이전트)
  - [CHAP7_multi-agent: 멀티 에이전트 시스템](#chap7_multi-agent-멀티-에이전트-시스템)
  - [CHAP8_memory: 메모리 관리](#chap8_memory-메모리-관리)
  - [CHAP9_MCP: Model Context Protocol](#chap9_mcp-model-context-protocol)
  - [CHAP10_A2A: Agent-to-Agent 프로토콜](#chap10_a2a-agent-to-agent-프로토콜)
  - [CHAP11_final-project: 실전형 멀티 에이전트 시스템](#chap11_final-project-실전형-멀티-에이전트-시스템)
- [실행 방법](#실행-방법)
  - [1. 저장소 클론](#1-저장소-클론)
  - [2. 가상환경 구성](#2-가상환경-구성)
  - [3. 패키지 설치](#3-패키지-설치)
  - [4. 환경 변수 설정](#4-환경-변수-설정)
  - [5. LangGraph Studio 활용](#5-langgraph-studio-활용)
- [문의](#문의)

---

## 파일 구성

본 저장소는 책의 흐름에 따라 구성되어 있으며, 각 챕터별로 독립된 실습 환경을 제공합니다.

### PART2 (4-5장): 랭그래프 기초
```
PART2/
├── 4.4_main.py
├── 5.2_랭그래프 기본 개념 이해하기.ipynb
└── 5.3_랭그래프로 에이전트 설계하고 구현하기.ipynb
```

### CHAP6_single-agent: 싱글 에이전트
```
CHAP6_single-agent/
├── coding_agent/          # 6.3 코딩 에이전트 만들기
├── rag_agent/            # 6.5 RAG를 위한 에이전트 만들기
├── web_agent/            # 6.2 웹 검색 에이전트 만들기
├── create_agent/         # 6.4 create_agent 상세 구조 이해하기
└── langgraph.json
```

### CHAP7_multi-agent: 멀티 에이전트 시스템
```
CHAP7_multi-agent/
├── supervisor_agent_web/        # 7.4 웹페이지를 요약해서 데이터베이스에 저장하는 에이전트
├── supervisor_agent_triple/      # 7.5 최신 문서 검색 + 내부 DB 검색 + 템플릿 답변 3중 멀티 에이전트
├── supervisor_planning_agent/    # 7.6 자료 조사 전문가 + 문서 작성 전문가 에이전트
├── network_agent/               # 7.3 정보 검색을 기반으로 차트를 그려주는 에이전트
├── how_to_use_command.ipynb
├── outputs/
└── langgraph.json
```

### CHAP8_memory: 메모리 관리
```
CHAP8_memory/
├── short-term memory.ipynb
└── long-term memory.ipynb
```

### CHAP9_MCP: Model Context Protocol
```
CHAP9_MCP/
├── mcp_agent/              # 9.3, 9.4
└── mcp_multi_agent/        # 9.5 랭그래프에서 MCP 기반 멀티 에이전트 구현하기
```

### CHAP10_A2A: Agent-to-Agent 프로토콜
```
CHAP10_A2A/
├── hello_world/           # 10.3 A2A의 기본 사용법 이해하기
└── multi_agent/           # 10.4 MCP와 A2A를 활용한 멀티 에이전트 구축하기
```

### CHAP11_final-project: 실전형 멀티 에이전트 시스템
```
CHAP11_final-project/        # [PART 5] 실전 멀티 에이전트 프로젝트
├── orchestrator_agent/
├── web_research_agent/
├── internal_rag_agent/
├── file_management_agent/
├── common/
├── test_client.py
└── README.md
```

## 실행 방법

파이썬 개발 경험 입문자라면 책의 4장을 참고하여 개발 환경을 순차적으로 따라오시길 권장드리며, 개발 환경 셋팅에 대한 이해도가 있으신 분들은 uv 기반 패키지 관리를 권장드립니다.

- Python 3.11 이상

### 1. 저장소 클론

```bash
git clone https://github.com/gongwon-nayeon/hanbit-aiagent.git
```

### 2. 가상환경 구성

#### 아나콘다 가상 환경 구성하기 (책 4장 참고)

```bash
C:/Users/…/anaconda3/Scipts/activate
conda --version
conda create -n langgraph python=3.12
conda activate langgraph
```

#### uv 사용하여 패키지 관리하기

```bash
# uv 설치 (Windows)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# uv 설치 (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```
# 가상환경 생성 및 활성화
uv venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

```
uv sync
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```


### 3. 패키지 설치

**방법 1: pyproject.toml 사용 (권장)**
```bash
# uv 사용
uv pip install -e .
```

**방법 2: requirements.txt 사용**
```bash
# pip 사용
pip install -r requirements.txt

# uv 사용
uv pip install -r requirements.txt
```

### 4. 환경 변수 설정

각 챕터의 루트 디렉터리에 `.env` 파일을 생성하고 필요한 API 키를 설정합니다.

```
copy .env.example .env
```

### 5. LangGraph Studio 활용

`langgraph dev` 명령어를 사용하여 LangGraph Studio에서 에이전트를 시각화하고 테스트할 수 있습니다.
더 자세한 설명은 책의 **6.2.5절 [실습] 랭그래프 서버 실행하고 랭그래프 스튜디오 사용하기** 를 참고해주세요.

#### langgraph.json 파일 작성

각 챕터의 루트 디렉터리에 `langgraph.json` 파일을 생성하여 에이전트를 설정합니다.

**기본 구조:**
```json
{
  "dependencies": ["./agent_directory"],
  "graphs": {
    "agent": "./agent_directory/agent.py:graph"
  },
  "env": ".env"
}
```

- `dependencies`: 에이전트 코드가 있는 디렉터리 경로
- `graphs`: 에이전트 그래프 객체의 위치 (파일경로:변수명)
- `env`: 환경 변수 파일 경로

**실행 방법:**
```bash
# 해당 챕터 디렉터리로 이동
cd CHAP6_single-agent

# LangGraph Studio 실행
langgraph dev
# uv run langraph dev
```

## 문의

### GitHub Issues
코드 실행 중 문제가 발생하거나 질문이 있으시면 GitHub Issues를 활용해주세요. 질의응답 커뮤니티로 활용하실 수 있습니다.

[이슈 등록하기](https://github.com/gongwon-nayeon/hanbit-aiagent/issues)

### 저자 연락처
- 이메일: uoahvu@gmail.com
- 유튜브 채널: [**공원나연**](https://www.youtube.com/@gongwon-nayeon)

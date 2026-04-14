# A2A 프로토콜 Hello World 예제

### 1단계: 에이전트 서버 실행

```bash
python agent_server.py
```

서버가 `http://localhost:9999`에서 실행됩니다.

### 2단계: 클라이언트로 에이전트와 통신

새로운 터미널에서 아래 명령어를 실행합니다.

```bash
python test_client.py
```

## 파일 구조

```
hello_world/
├── README.md
├── agent_server.py        # A2A 에이전트 서버 구현
├── agent_executor.py      # 에이전트 실행 로직
└── test_client.py         # 테스트 클라이언트
```
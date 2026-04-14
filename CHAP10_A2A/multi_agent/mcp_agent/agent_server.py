import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent_executor import MCPAgentExecutor


def create_agent_card() -> AgentCard: # [ 1 ]
    """
    에이전트 카드 생성

    Returns:
        AgentCard: MCP 에이전트 정보 카드
    """
    # 에이전트가 수행할 수 있는 작업 정의
    skill = AgentSkill(
        id='mcp_tavily_search',
        name='Tavily 웹 검색 에이전트',
        description='Tavily MCP 서버를 통해 웹 검색을 수행하고 최신 정보를 제공합니다',
        tags=['mcp', 'tavily', 'web search', 'internet'],
        examples=['파이썬 최신 트렌드 알려줘', 'AI 에이전트란?', '2025년 기술 동향 검색해줘'],
    )

    # 에이전트의 기술적 능력
    capabilities = AgentCapabilities( # [ 2 ]
        streaming=True,
        input_modes=['text'],
        output_modes=['text'],
    )

    # 에이전트 카드
    agent_card = AgentCard( # [ 3 ]
        name='Tavily MCP Search Agent',
        description='Tavily MCP 서버를 사용하여 웹 검색을 수행하는 에이전트입니다. LangGraph와 LangChain을 사용하지 않고 순수 MCP 프로토콜로 구현되었습니다.',
        url='http://localhost:10002',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=capabilities,
        skills=[skill],
    )

    return agent_card


def main():
    """
    A2A 에이전트 서버 시작
    """
    # 1. 에이전트 카드 생성
    agent_card = create_agent_card() # [ 4 ]

    # 2. 에이전트 실행자 생성
    agent_executor = MCPAgentExecutor()

    # 3. 작업 저장소 (메모리 기반)
    task_store = InMemoryTaskStore()

    # 4. 요청 처리기 생성
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=task_store,
    )

    # 5. A2A 서버 애플리케이션 생성
    server_app = A2AStarletteApplication( # [ 5 ]
        agent_card=agent_card,
        http_handler=request_handler,
    )

    # 6. 서버 실행
    print("=" * 60)
    print("Tavily MCP Search 에이전트 서버 시작")
    print("=" * 60)
    print(f"서버 주소: http://localhost:10002")
    print(f"에이전트 카드: http://localhost:10002/.well-known/agent-card.json")
    print("=" * 60)
    print("\n서버를 중지하려면 Ctrl+C를 누르세요\n")

    uvicorn.run(
        server_app.build(),
        host='0.0.0.0',
        port=10002,
    )


if __name__ == '__main__':
    main()

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent_executor import HelloWorldAgentExecutor


def create_agent_card() -> AgentCard:
    """
    에이전트 카드 생성

    AgentCard는 에이전트의 메타데이터를 담고 있으며,
    클라이언트가 에이전트의 기능을 파악할 수 있게 합니다.

    Returns:
        AgentCard: 에이전트 정보 카드
    """
    # AgentSkill: 에이전트가 수행할 수 있는 작업 정의
    skill = AgentSkill( # [ 1 ]
        id='hello_world',
        name='Hello World 인사',
        description='간단한 인사말을 반환합니다',
        tags=['인사', 'hello world', '기본'],
        examples=['안녕', '안녕하세요', 'hi', 'hello'],
    )

    # AgentCapabilities: 에이전트의 기술적 능력
    capabilities = AgentCapabilities( # [ 2 ]
        streaming=False,  # 스트리밍 지원 여부
        input_modes=['text'],  # 입력 형식
        output_modes=['text'],  # 출력 형식
    )

    # AgentCard: 에이전트의 전체 정보
    agent_card = AgentCard( # [ 3 ]
        name='Hello World 에이전트',
        description='A2A 프로토콜을 학습하기 위한 가장 간단한 에이전트입니다',
        url='http://localhost:9999',
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

    이 함수는:
    1. AgentCard를 생성하여 에이전트 정보를 정의
    2. HelloWorldAgentExecutor로 에이전트 실행자를 생성
    3. DefaultRequestHandler로 요청 처리기를 생성
    4. A2AStarletteApplication으로 서버 애플리케이션을 구성
    5. uvicorn으로 서버를 실행
    """
    # 1. 에이전트 카드 생성
    agent_card = create_agent_card() # [ 1 ]

    # 2. 에이전트 실행자 생성
    agent_executor = HelloWorldAgentExecutor() # [ 2 ]

    # 3. 작업 저장소 (메모리 기반)
    task_store = InMemoryTaskStore() # [ 3 ]

    # 4. 요청 처리기 생성
    request_handler = DefaultRequestHandler( # [ 4 ]
        agent_executor=agent_executor,
        task_store=task_store,
    )

    # 5. A2A 서버 애플리케이션 생성
    server_app = A2AStarletteApplication( # [ 5 ]
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn.run( # [ 6 ]
        server_app.build(),
        host='0.0.0.0',
        port=9999,
    )


if __name__ == '__main__':
    main()

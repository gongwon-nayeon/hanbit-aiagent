import logging
import uvicorn
from a2a.server.apps import A2AStarletteApplication

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent_executor import OrchestratorAgentExecutor


def create_agent_card() -> AgentCard:
    """에이전트 카드 생성"""

    routing_skill = AgentSkill(
        id='orchestrator_routing',
        name='Intent 분석 & 라우팅',
        description='사용자 질문을 분석하고 적절한 에이전트로 라우팅합니다',
        tags=['routing', 'intent', 'analysis'],
        examples=[
            '최신 AI 트렌드 알려줘',
            '우리 회사 휴가 정책 알려줘',
            '이 파일을 드라이브에 업로드해줘'
        ],
    )

    planning_skill = AgentSkill(
        id='orchestrator_planning',
        name='멀티스텝 플래닝',
        description='복잡한 작업을 여러 단계로 분해하고 순서대로 실행합니다',
        tags=['planning', 'multi-step', 'coordination'],
        examples=[
            '파일을 업로드하고 내용을 검색해서 요약해줘',
            '외부 정보와 사내 문서를 비교 분석해줘'
        ],
    )

    capabilities = AgentCapabilities(
        streaming=True,
        input_modes=['text'],
        output_modes=['text'],
    )

    agent_card = AgentCard(
        name='Orchestrator Agent',
        description='사용자 요청을 분석하고 여러 전문 에이전트를 조율하는 중앙 오케스트레이터',
        url='http://localhost:10010',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=capabilities,
        skills=[routing_skill, planning_skill],
    )

    return agent_card


def main():
    """서버 시작"""
    agent_card = create_agent_card()
    agent_executor = OrchestratorAgentExecutor()
    task_store = InMemoryTaskStore()

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=task_store,
    )

    server_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    logger.info("=" * 60)
    logger.info("[ORCHESTRATOR AGENT] 서버 시작")
    logger.info("=" * 60)
    logger.info("[ORCHESTRATOR AGENT] 서버 주소: http://localhost:10010")
    logger.info("[ORCHESTRATOR AGENT] 에이전트 카드: http://localhost:10010/.well-known/agent-card.json")
    logger.info("=" * 60)
    logger.info("[ORCHESTRATOR AGENT] 서버를 중지하려면 Ctrl+C를 누르세요")

    uvicorn.run(
        server_app.build(),
        host='0.0.0.0',
        port=10010,
    )


if __name__ == '__main__':
    main()

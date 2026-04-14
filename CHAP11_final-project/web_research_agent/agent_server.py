import logging
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent_executor import WebResearchAgentExecutor


def create_agent_card() -> AgentCard:
    """에이전트 카드 생성"""

    web_search_skill = AgentSkill(
        id='web_search',
        name='웹 검색',
        description='웹에서 최신 정보를 검색하고 요약합니다',
        tags=['search', 'web', 'internet', 'news'],
        examples=[
            '2025년 AI 트렌드 검색해줘',
            '최신 파이썬 업데이트 알려줘',
            'OpenAI GPT 최신 뉴스'
        ],
    )

    news_search_skill = AgentSkill(
        id='news_search',
        name='뉴스 검색',
        description='최신 뉴스를 검색하고 요약합니다',
        tags=['news', 'current events', 'updates'],
        examples=[
            '오늘 IT 뉴스 알려줘',
            '최신 기술 뉴스'
        ],
    )

    url_fetch_skill = AgentSkill(
        id='url_fetch',
        name='URL 내용 가져오기',
        description='특정 URL의 내용을 가져와 분석합니다',
        tags=['url', 'webpage', 'fetch'],
        examples=[
            'https://example.com 내용 가져와줘'
        ],
    )

    capabilities = AgentCapabilities(
        streaming=True,
        input_modes=['text'],
        output_modes=['text'],
    )

    agent_card = AgentCard(
        name='Web Research Agent',
        description='MCP 기반 외부 웹 검색 및 정보 수집 에이전트. Tavily API를 사용하여 최신 웹 정보를 검색하고 요약합니다.',
        url='http://localhost:10011',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=capabilities,
        skills=[web_search_skill, news_search_skill, url_fetch_skill],
    )

    return agent_card


def main():
    """서버 시작"""
    agent_card = create_agent_card()
    agent_executor = WebResearchAgentExecutor()
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
    logger.info("[WEB AGENT] 서버 시작")
    logger.info("=" * 60)
    logger.info("[WEB AGENT] 서버 주소: http://localhost:10011")
    logger.info("[WEB AGENT] 에이전트 카드: http://localhost:10011/.well-known/agent-card.json")
    logger.info("=" * 60)
    logger.info("[WEB AGENT] 서버를 중지하려면 Ctrl+C를 누르세요")

    uvicorn.run(
        server_app.build(),
        host='0.0.0.0',
        port=10011,
    )


if __name__ == '__main__':
    main()

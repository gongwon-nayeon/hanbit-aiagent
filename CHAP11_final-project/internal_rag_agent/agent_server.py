import logging
import uvicorn

# 로깅 설정
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
from agent_executor import InternalRAGAgentExecutor


def create_agent_card() -> AgentCard:
    """에이전트 카드 생성"""

    vector_search_skill = AgentSkill( # [ 1 ]
        id='rag_vector_search',
        name='벡터 검색 (의미 기반) 기반 답변',
        description='사내 문서를 의미 기반으로 검색하고 질문에 답변합니다. 자연어 질문, 개념 설명 등에 사용됩니다.',
        tags=['search', 'vector', 'semantic', 'rag', 'qa'],
        examples=[
            'AI 트렌드 관련 문서 찾아줘',
            '보안 정책이 뭐야?'
        ],
    )

    sql_search_skill = AgentSkill(
        id='rag_sql_search',
        name='SQL 검색 (메타데이터) 기반 답변',
        description='문서 메타데이터 조건으로 검색합니다. 문서 유형, 작성 날짜 등 구조화된 정보로 필터링할 때 사용됩니다.',
        tags=['search', 'sql', 'metadata', 'filter'],
        examples=[
            '2025년 12월에 작성된 텍스트 문서',
            'PDF 파일 중에서 가장 최근 문서'
        ],
    )

    index_skill = AgentSkill(
        id='rag_index',
        name='문서 인덱싱',
        description='Google Drive 파일을 다운로드하여 텍스트 추출 후 벡터 DB에 인덱싱합니다. storage_ref (gdrive://file/xxx)로 파일을 지정하면 자동으로 청킹, 임베딩하여 저장합니다.',
        tags=['index', 'embedding', 'chunking', 'storage'],
        examples=[
            '이 파일을 인덱싱해줘: 보고서.pdf (gdrive://file/abc123)',
            'reports 폴더 파일들 전부 인덱싱해줘',
            '다음 파일 하나만 인덱싱: 정책.docx (gdrive://file/xyz789)'
        ],
    )

    capabilities = AgentCapabilities( # [ 2 ]
        streaming=True,
        input_modes=['text'],
        output_modes=['text'],
    )

    agent_card = AgentCard( # [ 3 ]
        name='Internal RAG Agent',
        description='사내 문서/DB 기반 RAG 검색 및 인덱싱 에이전트. 벡터 검색(의미 기반), SQL 검색(메타데이터), 문서 인덱싱을 담당합니다.',
        url='http://localhost:10012',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=capabilities,
        skills=[vector_search_skill, sql_search_skill, index_skill],
    )

    return agent_card


def main():
    """서버 시작"""
    agent_card = create_agent_card()
    agent_executor = InternalRAGAgentExecutor()
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
    logger.info("[RAG AGENT] 서버 시작")
    logger.info("=" * 60)
    logger.info("[RAG AGENT] 서버 주소: http://localhost:10012")
    logger.info("[RAG AGENT] 에이전트 카드: http://localhost:10012/.well-known/agent-card.json")
    logger.info("=" * 60)
    logger.info("[RAG AGENT] 서버를 중지하려면 Ctrl+C를 누르세요")

    uvicorn.run(
        server_app.build(),
        host='0.0.0.0',
        port=10012,
    )


if __name__ == '__main__':
    main()

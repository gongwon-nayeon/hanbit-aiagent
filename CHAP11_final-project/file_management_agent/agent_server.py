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
from agent_executor import FileManagementAgentExecutor


def create_agent_card() -> AgentCard:
    """에이전트 카드 생성"""

    upload_skill = AgentSkill( # [ 1 ]
        id='upload_file',
        name='파일 업로드',
        description='Google Drive에 파일을 업로드합니다. 특정 폴더에 저장하려면 folder_id를 지정할 수 있습니다.',
        tags=['upload', 'file', 'gdrive', 'save'],
        examples=[
            '이 내용을 report.txt로 드라이브에 저장해줘',
            '문서를 업로드해줘',
            'projects 폴더에 파일 저장해줘'
        ],
    )

    download_skill = AgentSkill(
        id='download_file_as_base64',
        name='파일 다운로드 (Base64)',
        description='Google Drive에서 파일을 다운로드하여 Base64로 인코딩하여 반환합니다.',
        tags=['download', 'file', 'read', 'get', 'base64'],
        examples=[
            '문서 다운로드해서 내용 알려줘',
            '벡터 인덱스를 위한 파일을 base64로 받아줘'
        ],
    )

    get_info_skill = AgentSkill(
        id='get_file_info',
        name='파일 정보 조회',
        description='Google Drive 파일의 상세 정보를 조회합니다. 파일명, 크기, 생성일, MIME 타입 등을 확인합니다.',
        tags=['info', 'metadata', 'details'],
        examples=[
            '파일 정보 알려줘',
            '이 파일 언제 만들어졌어?',
            '파일 크기 확인해줘'
        ],
    )

    find_folder_skill = AgentSkill(
        id='find_folder',
        name='폴더 조회',
        description='Google Drive에서 특정 이름의 폴더를 조회합니다. 상위 폴더를 지정하여 하위 폴더를 검색할 수도 있습니다.',
        tags=['find', 'folder', 'directory', 'search'],
        examples=[
            'projects 폴더 찾아줘',
            '문서 폴더 어디에 있어?'
        ],
    )

    list_skill = AgentSkill(
        id='list_files',
        name='파일 목록 조회',
        description='Google Drive의 파일 목록을 조회합니다. 검색어로 파일명을 필터링하거나, 특정 폴더 내 파일만 조회할 수 있습니다.',
        tags=['list', 'files', 'browse', 'search'],
        examples=[
            '파일 목록 보여줘',
            'report가 들어간 파일 찾아줘',
            'projects 폴더 안에 뭐가 있어?'
        ],
    )

    delete_skill = AgentSkill(
        id='delete_file',
        name='파일 삭제',
        description='Google Drive에서 파일을 삭제합니다. 기본적으로 휴지통으로 이동하며, permanent=True면 영구 삭제합니다.',
        tags=['delete', 'remove', 'trash'],
        examples=[
            '이 파일 삭제해줘',
            '휴지통으로 보내줘',
            '파일 영구 삭제해줘'
        ],
    )

    update_skill = AgentSkill(
        id='update_file',
        name='파일 업데이트',
        description='Google Drive 파일을 업데이트합니다. 파일 내용이나 파일명을 변경할 수 있습니다.',
        tags=['update', 'edit', 'modify', 'rename'],
        examples=[
            '파일 내용 수정해줘',
            '파일 이름 바꿔줘',
            '새 버전으로 업데이트해줘'
        ],
    )

    create_folder_skill = AgentSkill(
        id='create_folder',
        name='폴더 생성',
        description='Google Drive에 새 폴더를 생성합니다.',
        tags=['folder', 'directory', 'create'],
        examples=[
            '새 폴더 만들어줘',
            'projects 폴더 생성해줘',
            '디렉토리 만들어줘'
        ],
    )

    capabilities = AgentCapabilities( # [ 2 ]
        streaming=True,
        input_modes=['text'],
        output_modes=['text'],
    )

    agent_card = AgentCard( # [ 3 ]
        name='File Management Agent',
        description='Google Drive 기반 파일 관리 에이전트. 파일 업로드/다운로드, 목록 조회, 삭제, 업데이트, 폴더 생성을 지원합니다. storage_ref 형식: gdrive://file/{FILE_ID}',
        url='http://localhost:10013',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=capabilities,
        skills=[upload_skill, download_skill, get_info_skill, find_folder_skill, list_skill, delete_skill, update_skill, create_folder_skill],
    )

    return agent_card


def main():
    agent_card = create_agent_card()
    agent_executor = FileManagementAgentExecutor()
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
    logger.info("[FILE AGENT] 서버 시작")
    logger.info("=" * 60)
    logger.info("[FILE AGENT] 서버 주소: http://localhost:10013")
    logger.info("[FILE AGENT] 에이전트 카드: http://localhost:10013/.well-known/agent-card.json")
    logger.info("=" * 60)
    logger.info("[FILE AGENT] 서버를 중지하려면 Ctrl+C를 누르세요")

    uvicorn.run(
        server_app.build(),
        host='0.0.0.0',
        port=10013,
    )


if __name__ == '__main__':
    main()

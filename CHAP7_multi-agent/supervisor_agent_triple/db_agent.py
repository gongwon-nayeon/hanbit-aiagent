from langchain.tools import tool
from langchain.agents import create_agent
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import END
from dotenv import load_dotenv

from settings import get_model

load_dotenv()

DB_PATH = "./supervisor_agent_triple/chroma_db" # [ 1 ]

persist_db = Chroma(
    persist_directory=DB_PATH,
    embedding_function=OpenAIEmbeddings(),
    collection_name="documents",
)
persist_db.get()

@tool
def list_all_documents() -> str: # [ 2 ]
    """
    데이터베이스에 저장된 모든 문서 목록을 확인하는 도구입니다.

    Returns:
        저장된 문서들의 목록과 청크 수
    """
    try:
        all_data = persist_db.get()

        if not all_data or not all_data['metadatas']:
            return "저장된 문서가 없습니다."

        # 파일별로 그룹화
        file_info = {}
        for metadata in all_data['metadatas']:
            file_name = metadata.get('file_name', 'Unknown')
            file_type = metadata.get('file_type', 'Unknown')

            if file_name not in file_info:
                file_info[file_name] = {
                    'type': file_type,
                    'count': 0
                }
            file_info[file_name]['count'] += 1

        response = f"총 {len(file_info)}개의 문서가 저장되어 있습니다:\n\n"
        for i, (file_name, info) in enumerate(file_info.items(), 1):
            response += f"{i}. {file_name} ({info['type']}) - {info['count']}개 청크\n"

        return response
    except Exception as e:
        return f"문서 목록 조회 중 오류가 발생했습니다: {str(e)}"


@tool
def vector_retriever(query: str, filename: str = "") -> str:
    """
    벡터 데이터베이스에서 정보를 검색하는 도구입니다.
    내용뿐만 아니라 문서 제목(파일명)으로도 검색이 가능합니다.
    특정 파일 내에서만 검색하려면 filename 파라미터를 사용합니다.

    Args:
        query: 검색할 내용 (키워드, 문서 제목, 또는 문장)
        filename: (선택) 검색 대상 파일명. 제공하면 해당 파일 내에서만 검색합니다.
                  예: "example.docx" 또는 "example" (확장자 생략 가능)

    Returns:
        검색 결과
    """
    try:
        if filename: # [ 1 ]
            results = persist_db.similarity_search(
                query=query,
                k=10,
                filter={"file_name": filename}
            )
        else: # [ 2 ]
            results = persist_db.similarity_search(
                query=query,
                k=10
            )

        if not results:
            return "검색 결과가 없습니다."

        file_groups = {} # [ 3 ]
        for doc in results:
            file_name = doc.metadata.get('file_name', 'Unknown')
            if file_name not in file_groups:
                file_groups[file_name] = []
            file_groups[file_name].append(doc)

        response = f"'{filename}' 파일 내 검색 결과:\n\n"
        max_per_file = 5

        result_num = 1 # [ 4 ]
        for file_name, docs in file_groups.items():
            for doc in docs[:max_per_file]:
                response += f"[결과 {result_num}]\n"
                response += f"파일: {doc.metadata.get('file_name', 'Unknown')}\n"
                response += f"타입: {doc.metadata.get('file_type', 'Unknown')}\n"
                if 'page' in doc.metadata:
                    response += f"페이지: {doc.metadata['page']}\n"

                content = doc.page_content
                response += f"내용: {content}\n\n"
                result_num += 1

        return response
    except Exception as e:
        return f"검색 중 오류가 발생했습니다: {str(e)}"


model = get_model(model_name="gpt-4o")
tools = [vector_retriever, list_all_documents]

db_agent = create_agent(
    model=model,
    tools=tools,
    system_prompt="""
    당신은 문서 검색 전문 에이전트입니다.

    주요 역할:
    - PDF 및 Word 문서에서 관련 정보 검색
    - 문서 제목(파일명)으로도 검색 가능
    - 특정 파일 내에서만 검색 가능

    list_all_documents 도구를 사용해 어떤 문서를 가지고 있는 지 먼저 확인하세요.
    검색 결과를 바탕으로 사용자에게 도움이 되는 명확하고 구체적인 답변을 제공하세요.
    """
)


from langgraph.types import Command
from langchain.messages import HumanMessage
from handoff_tools import create_handoff_messages
from settings import AgentState


def create_db_search_agent(state: AgentState) -> Command:
    query = state.get("query", "")
    agent_state = {"messages": [HumanMessage(content=query)]}

    result = db_agent.invoke(agent_state)

    ai_message, tool_message = create_handoff_messages("db_search")

    result["messages"].extend([ai_message, tool_message])

    return Command(
        update={"messages": result["messages"]},
        goto=END,
    )

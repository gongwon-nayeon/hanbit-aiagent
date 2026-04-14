from typing import List
from langchain_core.tools import tool
from langchain_core.messages import AIMessage
from langchain_community.document_loaders import WebBaseLoader
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from settings import get_model

_loaded_web_content = []

def _clean_content(content: str) -> str:
    """
    웹 콘텐츠에서 불필요한 요소를 제거하고 정리합니다.

    Args:
        content: 정리할 원본 콘텐츠

    Returns:
        정리된 콘텐츠
    """

    llm = get_model("gpt-4o-mini")

    cleaning_prompt = f"""다음 웹페이지에서 추출한 텍스트를 정리해주세요.

    원본 텍스트:
    {content}

    지시사항:
    1. 불필요한 공백, 개행 문자를 정리하여 읽기 쉽게 만들기
    2. 광고 텍스트, 네비게이션 메뉴, 푸터 정보 등 본문과 무관한 내용 삭제
    3. 핵심 내용만 남기고 중복되거나 불필요한 텍스트 제거
    4. 문단 구조를 유지하면서 정돈된 형태로 반환
    5. 중요한 정보(제목, 본문 내용, 핵심 데이터)는 반드시 유지

    정리된 텍스트만 반환해주세요 (추가 설명 없이):"""

    response = llm.invoke(cleaning_prompt)
    cleaned_content = response.content.strip()
    return cleaned_content

@tool
def web_content_loader(
    urls: List[str]
):
    """
    WebBaseLoader를 사용하여 웹사이트의 내용을 가져오는 도구입니다.

    Args:
        urls (List[str]): 크롤링할 웹사이트 URL들 목록

    Returns:
        str: 각 웹사이트의 제목과 정리된 내용
    """
    try:
        loader = WebBaseLoader(urls) # [ 1 ]
        all_docs = loader.load()

        if not all_docs:
            return "웹사이트 내용을 가져올 수 없습니다. URL을 확인해주세요."

        result = []
        for doc in all_docs: # [ 2 ]
            cleaned_content = _clean_content(doc.page_content)

            result.append({
                "url": doc.metadata.get('source', 'No url'),
                "title": doc.metadata.get('title', 'No title'),
                "full_content": cleaned_content,
                "content_length": len(cleaned_content)
            })

        global _loaded_web_content # [ 3 ]
        _loaded_web_content = result

        return result

    except Exception as e:
        return f"웹사이트 크롤링에 실패했습니다. 오류: {repr(e)}"


def chatbot(state: MessagesState):
    messages = [ # [ 4 ]
        {
            "role": "system",
            "content": """
            당신은 URL 추출과 웹 크롤링 전문가입니다.
            사용자의 메시지에서 URL을 찾아내고, web_content_loader 도구를 사용하여 해당 웹페이지의 내용을 가져오세요.
            여러 개의 URL을 발견한 경우, 반드시 모든 URL을 하나의 리스트로 묶어서 web_content_loader를 한번만 호출하세요.
            """
        },
    ] + state["messages"]

    llm = get_model("gpt-4o")
    result = llm.bind_tools([web_content_loader]).invoke(messages) # [ 5 ]

    return {"messages": [result]}


def question_generator_node(state: MessagesState):
    """로드된 웹 페이지의 내용을 기반으로 확장 질문을 생성하는 노드"""
    global _loaded_web_content

    combined_content = "" # [ 1 ]
    for content_item in _loaded_web_content:
        if isinstance(content_item, dict):
            url = content_item.get("url", "Unknown URL")
            title = content_item.get("title", "No title")
            full_content = content_item.get("full_content", "")  # 정제된 콘텐츠 사용
            combined_content += f"URL: {url}\n제목: {title}\n\n{full_content}\n\n{'='*80}\n\n"
    # [ 2 ]
    prompt = f"""
    다음 웹 페이지 내용을 바탕으로, 사용자가 관심 있을만한 확장 질문을 생성해주세요.

    웹 페이지 내용:
    {combined_content}

    요구사항:
    1. 웹 페이지 내용을 기반으로 추가로 궁금한 질문들
    2. 한국어로 작성
    3. 각 질문은 번호를 매겨서 url과 함께 딕셔너리 형태로 제공
    4. url 별로 1-2 개의 질문을 생성
    """
    llm = get_model("gpt-4o-mini")
    response = llm.invoke(prompt)
    questions = response.content

    result_message = f"웹 페이지 내용을 기반으로 사용자에게 다음 질문을 추가로 생각해보도록 제안할 수 있습니다. : \n\n{questions}\n"

    return {"messages": [AIMessage(content=result_message, name="web_agent")]} # [ 3 ]


def create_workflow() -> CompiledStateGraph:
    graph_builder = StateGraph(MessagesState)

    graph_builder.add_node("chatbot", chatbot)
    tool_node = ToolNode(tools=[web_content_loader])
    graph_builder.add_node("url_extractor", tool_node)
    graph_builder.add_node("question_generator", question_generator_node)

    graph_builder.add_edge(START, "chatbot") # [ 1 ]
    graph_builder.add_conditional_edges( # [ 2 ]
        "chatbot",
        tools_condition,
        {"tools": "url_extractor", END: END}
    )
    graph_builder.add_edge("url_extractor", "question_generator") # [ 3 ]
    graph_builder.add_edge("question_generator", END) # [ 4 ]

    return graph_builder.compile()

web_node = create_workflow()

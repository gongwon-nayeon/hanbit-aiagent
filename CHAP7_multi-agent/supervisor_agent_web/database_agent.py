from typing import List, Literal

from langchain.tools import tool
from langchain.agents import create_agent
from langgraph.types import Command
from langgraph.graph import MessagesState

from supabase import create_client

import os

from settings import get_model

def get_supabase_client(): # [ 1 ]
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    return create_client(url, key)

@tool
def save_web_data( # [ 2 ]
    url: str,
    title: str,
    content: str,
    questions: List[str] = None
):
    """
    웹사이트 내용과 확장 질문을 web_content 테이블에 저장합니다. web_agent에서 처리한 데이터를 저장할 때 사용합니다.

    Args:
        url (str): 웹사이트 URL
        title (str): 웹페이지 제목
        content (str): 웹페이지 전체 내용
        questions (List[str]): 생성된 확장 질문들의 리스트

    Returns:
        str: 저장 결과 메시지
    """
    try:
        supabase = get_supabase_client()

        questions_text = "\n".join(questions) if questions else "" # [ 3 ]

        web_content_data = {
            "url": url,
            "title": title,
            "content": content,
            "content_length": len(content),
            "questions": questions_text
        }

        response = supabase.table("web_content").insert(web_content_data).execute() # [ 4 ]

        result = [] # [ 5 ]
        result.append(f"웹 데이터가 성공적으로 저장되었습니다.")
        result.append(f"   - ID: {response.data[0]['id']}")
        result.append(f"   - URL: {url}")
        result.append(f"   - 제목: {title}")
        return '\n'.join(result)

    except Exception as e:
        return f"웹 데이터 저장에 실패했습니다. 오류: {repr(e)}"

@tool
def search_web_data( # [ 1 ]
    keyword: str = ""
):
    """
    web_content 테이블의 title 컬럼에서 Full Text Search로 검색합니다.

    Args:
        keyword (str): 검색 키워드

    Returns:
        str: 검색 결과 요약 및 안내 메시지
    """
    try:
        supabase = get_supabase_client()

        # Full Text Search: title 컬럼에서 검색
        # textSearch 메서드 사용 (Supabase의 PostgreSQL FTS)
        response = supabase.table("web_content").select("*").text_search("title", f"'{keyword}'").execute() # [ 2 ]
        results = response.data if response.data else []

        if not results:
            return f"검색 결과가 없습니다. 키워드: '{keyword}'"

        result_text = [] # [ 3 ]
        result_text.append(f"검색 결과 ({len(results)}개):")
        result_text.append(f"   - 키워드: '{keyword}'\n")

        for item in results:
            result_text.append(f"   - ID: {item['id']}")
            result_text.append(f"   - 생성일: {item['created_at']}")
            result_text.append(f"   - URL: {item['url']}")
            result_text.append(f"   - 제목: {item['title']}")
            result_text.append(f"   - 내용: {item['content']}")
            result_text.append("=" * 60)

        return '\n'.join(result_text)

    except Exception as e:
        return f"웹 데이터 검색에 실패했습니다. 오류: {repr(e)}"

llm = get_model("gpt-4o")

database_agent = create_agent(
    llm,
    [save_web_data, search_web_data],
    system_prompt="""
        당신은 웹 크롤링 데이터 전용 Supabase 데이터베이스 전문가입니다. 다른 어시스턴트들과 협력하여 작업합니다.
        web_content 테이블 하나만 사용하며, 이 테이블의 컬럼은 다음과 같습니다:
        - id: 고유 식별자
        - created_at: 생성 시간
        - url: 웹사이트 URL
        - title: 웹페이지 제목
        - content: 웹페이지 전체 내용
        - content_length: 내용 길이
        - questions: 생성된 확장 질문들

        웹 크롤링으로 수집한 데이터와 생성된 확장 질문들을 저장하거나,
        사용자의 요청 내 키워드를 기반으로 검색을 수행하고 결과를 반환합니다.
        검색 결과에는 각 항목의 URL, 제목, 내용을 포함합니다.
    """
)

def database_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    result = database_agent.invoke(state)

    result["messages"][-1].name = "database_agent"

    return Command(
        update={"messages": result["messages"]},
        goto="supervisor",
    )

from typing import Literal
from langchain.agents import create_agent
from langgraph.types import Command
from langchain_tavily import TavilySearch

from settings import get_model, State

tavily_search = TavilySearch(max_results=3) # [ 1 ]
agent = create_agent(
    get_model(),
    [tavily_search],
    system_prompt="""당신은 웹 검색과 자료 조사를 전담하는 연구 전문가입니다.

    주요 역할:
    1. 사용자가 요청한 주제에 대한 웹 검색 수행
    2. 관련 웹사이트에서 상세 정보 수집

    항상 정확하고 신뢰할 수 있는 정보 수집에 중점을 두세요."""
)

def research_node(state:State)-> Command[Literal["supervisor"]]: # [ 2 ]
    """Research 에이전트 노드"""

    result = agent.invoke(state)
    result["messages"][-1].name = "research_agent"

    return Command(
        goto="supervisor",
        update={"messages": result["messages"]}
    )

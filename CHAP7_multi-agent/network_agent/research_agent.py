from typing import Literal

from langchain_tavily import TavilySearch
from langchain.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.types import Command
from langgraph.graph import MessagesState, END

from settings import get_model, make_system_prompt

from dotenv import load_dotenv

load_dotenv()

llm = get_model()
tool = TavilySearch(max_results=5)

research_agent = create_agent(
    llm,
    tools=[tool],
    system_prompt=make_system_prompt(
        "당신은 웹검색을 통한 자료조사만 할 수 있습니다. 차트 시각화(html 파일 생성)를 담당하는 에이전트와 함께 일하고 있으니 차트 생성이나 파일 생성은 수행하지 말고 넘기세요."
    ),
)

def research_node(state: MessagesState) -> Command[Literal["html_generator", END]]:
    result = research_agent.invoke(state) # [ 1 ]

    result["messages"][-1] = HumanMessage( # [ 2 ]
        content=result["messages"][-1].content, name="researcher"
    )

    last_message = result["messages"][-1] # [ 3 ]
    if "최종 답변" in last_message.content:
        goto = END
    else:
        goto = "html_generator"

    return Command( # [ 4 ]
        update={"messages": result["messages"]},
        goto=goto,
    )

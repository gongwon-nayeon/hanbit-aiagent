from typing import Literal

from langchain.tools import tool
from langchain.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.types import Command
from langgraph.graph import MessagesState, END
from settings import get_model, make_system_prompt

llm = get_model()

@tool
def html_generator_tool(
    html_content: str,
    filename: str,
):
    # [ 1 ]
    """
    HTML 파일을 생성하고 저장합니다. 차트나 데이터 시각화를 HTML/CSS/JavaScript로 생성할 수 있습니다.

    Args:
        html_content (str): HTML 코드 내용
        filename (str): 저장할 HTML 파일명 (예: report.html)

    Returns:
        str: 파일 생성 결과 메시지
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f: # [ 2 ]
            f.write(html_content)
        return f"HTML 파일이 성공적으로 생성되었습니다: {filename}\n파일을 브라우저에서 열어 확인할 수 있습니다.\n\n작업이 완료되었다면 '최종 답변'으로 응답하세요."
    except Exception as e:
        return f"HTML 파일 생성에 실패하였습니다. 오류: {repr(e)}"

html_agent = create_agent( # [ 3 ]
    llm,
    [html_generator_tool],
    system_prompt=make_system_prompt(
        "당신은 HTML 파일을 생성하는 전문가입니다. 웹 기반 자료조사를 하는 에이전트와 함께 일하고 있습니다. "
        "데이터나 차트를 HTML/CSS/JavaScript를 사용해 시각화하고 파일로 저장할 수 있습니다. "
    ),
)

def html_node(state: MessagesState) -> Command[Literal["researcher", END]]:
    result = html_agent.invoke(state) # [ 1 ]

    result["messages"][-1] = HumanMessage( # [ 2 ]
        content=result["messages"][-1].content, name="html_generator"
    )
    last_message = result["messages"][-1]
    if "최종 답변" in last_message.content: # [ 3 ]
        goto = END
    else:
        goto = "researcher"

    return Command( # [ 4 ]
        update={"messages": result["messages"]},
        goto=goto,
    )

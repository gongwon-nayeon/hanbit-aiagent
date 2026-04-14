from typing import Literal, TypedDict
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command

from settings import get_model, SupervisorState

class Router(TypedDict): # [ 1 ]
    """작업을 수행할 에이전트를 라우팅합니다."""
    next: Literal["canvas", "research"]

def supervisor_node(state: SupervisorState) -> Command[Literal["canvas", "research", "planning"]]:
    """Supervisor 노드: 작업 할당 및 완료 관리를 통합 처리"""

    plan = state.get("plan", []) # [ 2 ]
    past_steps = state.get("past_steps", [])
    messages = state["messages"]

    # [ 3 ]
    try:
        task_description = plan[0]
    except IndexError:
        return Command(goto="planning", update={})

    recent_messages = "\n".join([
        f"{msg.name if hasattr(msg, 'name') else 'user'}: {msg.content}"
        for msg in messages[-3:] if messages
    ])

    print("recent_messages:", recent_messages)

    system_prompt = f"""
    당신은 멀티 에이전트 시스템의 수퍼바이저입니다. **오직 현재 작업만 관리**하세요.
    Router 도구를 사용하여 작업을 수행할 에이전트를 결정하세요.

    ## 현재 작업 (이것만 처리하세요):
    {task_description}

    ## 팀 멤버:
    - canvas: 글 작성, 목차 작성, 파일 저장을 담당
    - research: 웹 검색기반 분석, 자료 조사 등을 담당

    ## 최근 대화 내역:
    {recent_messages}
    **research_agent 혹은 canvas_agent가 이미 현재 작업 "{task_description}"을 완료했는지 판단**하고, 완료된 경우 또 다시 에이전트를 호출하지 말고 planning으로 돌아가세요.
    """

    llm = get_model()

    response = llm.bind_tools([Router]).invoke([{"role": "system", "content": system_prompt}]) # [ 4 ]

    if hasattr(response, "tool_calls") and len(response.tool_calls) > 0:
        router_args = response.tool_calls[0]["args"]
        goto = router_args["next"]

        task_message = HumanMessage(content=f"작업을 수행해주세요: {task_description}")

        return Command(
            goto=goto,
            update={
                "next": goto,
                "messages": [task_message]
            }
        )

    else: # [ 5 ]
        for msg in reversed(messages):
            if hasattr(msg, 'name') and msg.name in ["canvas_agent", "research_agent"]:
                supervisor_final_message = f"작업 '{task_description}'이 완료되었습니다.\n\n작업 결과:\n{msg.content}"
                break

        updated_past_steps = past_steps + [(task_description, supervisor_final_message)]

        completion_message = AIMessage(
            content=supervisor_final_message,
            name="supervisor"
        )

        return Command(
            goto="planning",
            update={
                "past_steps": updated_past_steps,
                "messages": [completion_message]
            }
        )

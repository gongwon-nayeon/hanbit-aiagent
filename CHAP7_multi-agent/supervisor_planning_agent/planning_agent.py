
from typing import List, Union
from langchain.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.types import Command
from langgraph.graph import END
from pydantic import BaseModel, Field

from settings import get_model, State

class Plan(BaseModel): # [ 1 ]
    """계획 수립을 위한 스키마"""

    steps: List[str] = Field(
        description="따라야 할 단계들, 정렬된 순서여야 함"
    )

class ConversationalResponse(BaseModel):
    """대화형 방식으로 응답하기 위한 스키마"""

    response: str = Field(description="사용자의 질문에 대한 대화형 응답")

class PlanningResponse(BaseModel):
    final_output: Union[Plan, ConversationalResponse]


def planning_node(state: State) -> Command:
    """Planning 노드: 계획 수립 및 작업 상태 관리"""

    messages = state["messages"] # [ 2 ]
    plan = state.get("plan", [])
    past_steps = state.get("past_steps", [])
    llm = get_model()

    # 첫 진입시: 계획 수립
    if not plan:
        planner_prompt = ChatPromptTemplate.from_messages([ # [ 3 ]
            (
                "system",
                """사용자의 요청을 분석하여 단계별 작업 계획을 세워주세요.
                계획은 논리적 순서로 배열하고, 각 단계가 독립적으로 실행 가능하도록 구성하세요.
                각 단계는 자료조사 에이전트와 글을 작성하는 에이전트가 협업하여 수행할 수 있으나, 하나의 태스크에 너무 많은 양의 작업이 몰리지 않도록 주의하세요.
                불필요한 단계는 추가하지 말고, 최종 단계의 결과가 사용자가 원하는 최종 답변이 되도록 하세요.
                단계의 개수는 2~5개 사이로 유지하세요.

                여러 단계의 작업이 필요없는 간단한 입력의 경우, 바로 답변할 수 있습니다.
                """
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])

        planner = planner_prompt | llm.with_structured_output(PlanningResponse) # [ 4 ]
        result = planner.invoke({"messages": messages})

        # 바로 답변할 수 있는 경우
        if isinstance(result.final_output, ConversationalResponse): # [ 5 ]
            response_message = AIMessage(
                content=result.final_output.response,
                name="planning"
            )
            return Command(
                goto=END,
                update={"messages": [response_message]}
            )

        # [ 6 ] Plan 객체인 경우 - 계획 수립
        generated_plan = result.final_output.steps

        if generated_plan:
            plan_list = "\n".join([f"{i+1}. {task}" for i, task in enumerate(generated_plan)])

            planning_message = AIMessage(
                content=f"작업 계획을 수립했습니다:\n{plan_list}",
                name="planning"
            )

            return Command(
                goto="supervisor",
                update={
                    "plan": generated_plan,
                    "messages": [planning_message]
                }
            )

    # 작업 완료 후 복귀: 계획 재검토
    else:
        past_steps_summary = "" # [ 1 ]
        if past_steps:
            past_steps_summary = "\n".join([f"- {task}: {result}" for task, result in past_steps])

        current_plan_text = "\n".join([f"{i+1}. {task}" for i, task in enumerate(plan)])

        replanner_prompt = ChatPromptTemplate.from_template( # [ 2 ]
            """주어진 목표에 대해 현재 상황을 분석하여 다음 중 하나를 선택하세요:

            1. 완료된 작업들을 바탕으로 사용자에게 최종 답변을 제공할 수 있는 경우
            2. 아직 더 수행해야 할 작업이 있는 경우

            목표:
            {input}

            현재 계획:
            {plan}

            현재까지 완료한 작업들:
            {past_steps}

            위 정보를 바탕으로 판단하세요:

            **모든 작업을 완료했거나, 완료된 작업들로 사용자의 목표를 충분히 달성했고 최종 답변을 제공할 수 있다면:**
            - ConversationalResponse로 사용자에게 도움이 되는 최종 답변을 제공하세요

            **만약 아직 더 수행해야 할 작업이 있다면:**
            - Plan으로 남은 작업들만 포함한 계획을 제공하세요
            - 불필요한 단계는 추가하지 말고, 최종 단계의 결과가 사용자가 원하는 최종 답변이 되도록 하세요.
            - 전체 단계의 개수는 2~5개 사이로 유지하세요.
            - 이미 완료된 작업은 포함하지 마세요
            - 각 단계는 'canvas' 에이전트(글 작성, 콘텐츠 생성, 파일 저장) 또는 'research' 에이전트(웹 검색, 정보 수집)가 수행할 수 있어야 합니다"""
        )

        replanner = replanner_prompt | llm.with_structured_output(PlanningResponse) # [ 3 ]
        replan_result = replanner.invoke({
            "input": messages[0].content if messages else "",
            "plan": current_plan_text,
            "past_steps": past_steps_summary if past_steps_summary else "아직 완료된 작업이 없습니다."
        })

        # 최종 답변 제공 가능한 경우
        if isinstance(replan_result.final_output, ConversationalResponse): # [ 4 ]
            response_message = AIMessage(
                content=replan_result.final_output.response,
                name="planning"
            )
            return Command(
                goto=END,
                update={"messages": [response_message]}
            )

        # Plan 객체인 경우 - 남은 작업들로 계획 업데이트
        remaining_plan = replan_result.final_output.steps

        status_message = AIMessage(
            content=f"계획을 업데이트했습니다. 다음 작업을 진행합니다:\n{remaining_plan[0]}",
            name="planning"
        )

        return Command(
            goto="supervisor",
            update={
                "plan": remaining_plan,
                "messages": [status_message]
            }
        )

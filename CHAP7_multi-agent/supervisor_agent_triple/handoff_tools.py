import uuid
from typing import cast
from langchain.tools import tool, ToolRuntime
from langchain.messages import AIMessage, ToolMessage
from langgraph.types import Command, Send


def create_handoff_tool(agent_name: str, description: str):
    """
    supervisor 에이전트에서 다른 에이전트로 작업을 handoff하는 도구를 생성합니다.
    """

    tool_name = f"transfer_to_{agent_name}" # [ 1 ]

    @tool(tool_name, description=description)
    def handoff_to_agent(
        query: str,
        runtime: ToolRuntime, # [ 2 ]
    ) -> Command:
        """
        에이전트로 작업을 handoff하는 도구입니다.

        Args:
            query: 에이전트에게 전달할 쿼리 (최대한 원본 쿼리를 유지)
            runtime: 도구 런타임 (런타임에서 자동 주입)
        """
        state = runtime.state # [ 3 ]
        tool_call_id = runtime.tool_call_id
        last_ai_message = cast(AIMessage, state["messages"][-1])

        # 2개 이상의 도구 호출: 모든 handoff 도구를 한번에 Send로 처리
        if len(last_ai_message.tool_calls) > 1:
            handoff_messages = state["messages"][:-1]

            # 모든 handoff 도구 호출을 수집
            send_list = []
            for tool_call in last_ai_message.tool_calls: # [ 4 ]
                # transfer_to_ 로 시작하는 handoff 도구만 처리
                if tool_call["name"].startswith("transfer_to_"):
                    target_agent = tool_call["name"].replace("transfer_to_", "")
                    query_content = tool_call['args'].get('query', '')

                    filtered_ai_message = AIMessage(
                        content=last_ai_message.content,
                        tool_calls=[tool_call],
                        name=last_ai_message.name,
                        id=str(uuid.uuid4()),
                    )

                    tool_msg = ToolMessage(
                        content=f"성공적으로 {target_agent}에게 작업을 전달했습니다: {query_content}",
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )

                    agent_messages = handoff_messages + [filtered_ai_message, tool_msg] # [ 5 ]
                    send_list.append(Send(target_agent, {
                        **state,
                        "messages": agent_messages,
                        "query": query_content
                    }))

            # 모든 에이전트에게 한번에 Send
            return Command(
                graph=Command.PARENT,
                goto=send_list,
            )

        # 1개 도구 호출: 바로 handoff 처리
        else: # [ 6 ]
            tool_message = ToolMessage(
                content=f"성공적으로 {agent_name}에게 작업을 전달했습니다: {query}",
                name=tool_name,
                tool_call_id=tool_call_id,
            )

            handoff_messages = state["messages"] + [tool_message]
            return Command(
                goto=agent_name,
                graph=Command.PARENT,
                update={**state, "messages": handoff_messages, "query": query}
            )

    return handoff_to_agent


def create_handoff_messages(agent_name: str):
    """
    에이전트에서 supervisor로 돌아갈 때 사용할 handoff back 메시지들을 생성합니다.

    Args:
        agent_name: 현재 에이전트 이름

    Returns:
        tuple: (AIMessage, ToolMessage) 쌍
    """
    tool_call_id = str(uuid.uuid4())
    tool_name = f"transfer_back_to_supervisor"

    ai_message = AIMessage(
        content=f"Supervisor로 이동합니다.",
        name=agent_name,
        tool_calls=[{
            "name": tool_name,
            "args": {},
            "id": tool_call_id
        }]
    )

    tool_message = ToolMessage(
        content=f"supervisor로 성공적으로 작업을 전달했습니다.",
        name=tool_name,
        tool_call_id=tool_call_id,
    )

    return ai_message, tool_message

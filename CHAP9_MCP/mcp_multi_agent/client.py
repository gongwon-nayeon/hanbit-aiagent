from dotenv import load_dotenv
import os
import asyncio
import sys

from typing import Literal
from typing_extensions import TypedDict

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent


import sys, asyncio
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o")

######################## GRAPH STATE ########################

class Router(TypedDict):
    """라우팅 할 작업자
    file_searcher: 파일 정보 호출 및 생성 작업자
    web_searcher: 웹 검색 작업자
    """

    next: Literal["file_searcher", "web_searcher"]


class State(MessagesState):
    next: str


async def run():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    client = MultiServerMCPClient(
        {
            "tavily": { # [ 1 ]
                "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}",
                "transport": "streamable_http",
            },
            "file": { # [ 2 ]
                "transport": "stdio",
                "command": "python",
                "args": ["./server.py"],
            }
        }
    )

    ######################## CHECK TOOLS ########################
    all_tools = await client.get_tools()
    print(f"Total tools loaded: {len(all_tools)}")
    print(f"Tool names: {[tool.name for tool in all_tools]}")

    tavily_tools = await client.get_tools(server_name="tavily")
    file_tools = await client.get_tools(server_name="file")

    print(f"Tavily tools: {[tool.name for tool in tavily_tools]}")
    print(f"File tools: {[tool.name for tool in file_tools]}")

    ######################## AGENT ########################
    members = ["file_searcher", "web_searcher"] # [ 1 ]

    system_prompt = f"""
당신은 다음 작업자들 간의 대화를 관리하는 슈퍼바이저입니다.
작업자들은 다음과 같습니다: {members}
특정 작업자가 수행할 작업이 있다면, Router 도구를 사용해 다음 작업자를 지정하세요.
작업이 필요없거나 즉시 답변하고, 이미 작업을 완료했다면 최종 답변을 반환하세요.
"""

    ######################## SUPERVISOR ########################
    async def supervisor_node( # [ 2 ]
        state: State,
    ) -> Command[Literal["file_searcher", "web_searcher", END]]:
        messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"]

        response = model.bind_tools([Router]).invoke(messages) # [ 3 ]

        if hasattr(response, "tool_calls") and len(response.tool_calls) > 0: # [ 4 ]
            goto = response.tool_calls[0]["args"]["next"]
            return Command(goto=goto, update={"next": goto})

        else: # [ 5 ]
            final_message = AIMessage(content=response.content, name="supervisor")
            return Command(
                goto=END,
                update={"messages": [final_message]}
            )

    ######################## 1) FILE SEARCHER ########################
    file_searcher = create_agent(model, file_tools) # [ 1 ]

    async def file_search_node(state: State) -> Command[Literal["supervisor"]]: # [ 2 ]
        result = await file_searcher.ainvoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content=result["messages"][-1].content, name="file_searcher"
                    )
                ]
            },
            goto="supervisor",
        )

    ######################## 2) WEB SEARCHER (TAVILY) ########################
    web_searcher = create_agent(model, tavily_tools) # [ 3 ]

    async def web_search_node(state: State) -> Command[Literal["supervisor"]]: # [ 4 ]
        result = await web_searcher.ainvoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content=result["messages"][-1].content, name="web_searcher"
                    )
                ]
            },
            goto="supervisor",
        )

    ######################## GRAPH COMPILE ########################
    graph_builder = StateGraph(State)
    graph_builder.add_edge(START, "supervisor")
    graph_builder.add_node("supervisor", supervisor_node)
    graph_builder.add_node("file_searcher", file_search_node)
    graph_builder.add_node("web_searcher", web_search_node)
    memory = InMemorySaver()
    graph = graph_builder.compile(checkpointer=memory)

    ######################## REQUEST & REPOND ########################
    config = {"configurable": {"thread_id": "1"}} # [ 1 ]
    while True:
        try:
            user_input = input("질문을 입력하세요: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("안녕히 가세요!")
                break

            async for _, chunk in graph.astream( # [ 2 ]
                {"messages": user_input},
                stream_mode="updates",
                subgraphs=True,
                config=config,
            ):
                for _, node_chunk in chunk.items(): # [ 3 ]
                    if "messages" in node_chunk:
                        node_chunk["messages"][-1].pretty_print()
                    else:
                        print(node_chunk)

        except Exception as e:
            print(f"종료합니다.{e}")
            break


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback

        traceback.print_exc()

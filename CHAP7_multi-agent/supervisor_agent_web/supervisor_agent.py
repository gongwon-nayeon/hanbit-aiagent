from typing import Literal, TypedDict
from langchain.messages import AIMessage
from langgraph.types import Command
from langgraph.graph import MessagesState, END

from settings import get_model, get_system_prompt

class Router(TypedDict): # [ 1 ]
    """다음으로 라우팅 할 작업자"""

    next: Literal["web_agent", "database_agent"]

class State(MessagesState):
    next: str

llm = get_model("gpt-4o")

def supervisor_node(state: State) -> Command[Literal["web_agent", "database_agent", END]]:
    messages = [ # [ 2 ]
        {"role": "system", "content": get_system_prompt(["web_agent", "database_agent"])},
    ] + state["messages"]

    response = llm.bind_tools([Router]).invoke(messages)

    if hasattr(response, "tool_calls") and len(response.tool_calls) > 0: # [ 3 ]
        goto = response.tool_calls[0]["args"]["next"]
        return Command(goto=goto, update={"next": goto})

    else: # [ 4 ]
        final_message = AIMessage(content=response.content, name="supervisor")
        return Command(
            goto=END,
            update={"messages": [final_message]}
        )

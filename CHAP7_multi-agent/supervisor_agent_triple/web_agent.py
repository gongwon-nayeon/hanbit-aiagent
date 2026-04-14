from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from langgraph.graph import END
from langgraph.types import Command
from langchain.messages import HumanMessage
from handoff_tools import create_handoff_messages
from settings import AgentState, get_model

model = get_model(model_name="gpt-4o") # [ 1 ]
tavily_search = TavilySearch(max_results=3)

web_agent = create_agent(
    model=model,
    tools=[tavily_search],
)

def create_web_agent(state: AgentState) -> Command: # [ 2 ]
    query = state.get("query", "")
    agent_state = {"messages": [HumanMessage(content=query)]}

    result = web_agent.invoke(agent_state)

    ai_message, tool_message = create_handoff_messages("web_search") # [ 3 ]

    result["messages"].extend([ai_message, tool_message])

    return Command( # [ 4 ]
        update={"messages": result["messages"]},
        goto=END,
    )

from langgraph.graph import StateGraph, MessagesState, END
from supervisor_agent import supervisor, agents

graph_builder = StateGraph(MessagesState) # [ 1 ]

agent_names = list(agents.keys()) # [ 2 ]
graph_builder.add_node(
    "supervisor",
    supervisor,
    destinations=tuple(agent_names) + (END,)
)
graph_builder.add_node("web_search", agents["web_search"]) # [ 3 ]
graph_builder.add_node("db_search", agents["db_search"])
graph_builder.add_node("faq", agents["faq"])

graph_builder.set_entry_point("supervisor")

for agent_name in agents.keys(): # [ 4 ]
    graph_builder.add_edge(agent_name, "supervisor")

graph = graph_builder.compile()

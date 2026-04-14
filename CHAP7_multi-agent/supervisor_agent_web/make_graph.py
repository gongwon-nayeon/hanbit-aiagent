from langgraph.graph import StateGraph, MessagesState, START
from supervisor_agent import supervisor_node
from web_agent import web_node
from database_agent import database_node

graph_builder = StateGraph(MessagesState)
graph_builder.add_edge(START, "supervisor")
graph_builder.add_node("supervisor", supervisor_node)
graph_builder.add_node("web_agent", web_node)
graph_builder.add_edge("web_agent", "supervisor")
graph_builder.add_node("database_agent", database_node)
graph = graph_builder.compile()

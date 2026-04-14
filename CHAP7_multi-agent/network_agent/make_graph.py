from langgraph.graph import StateGraph, MessagesState, START
from network_agent.research_agent import research_node
from network_agent.chart_agent import html_node

graph_builder = StateGraph(MessagesState)
graph_builder.add_node("researcher", research_node)
graph_builder.add_node("html_generator", html_node)

graph_builder.add_edge(START, "researcher")
graph = graph_builder.compile()

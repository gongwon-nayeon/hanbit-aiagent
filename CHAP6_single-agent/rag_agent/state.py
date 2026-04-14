from langgraph.graph import MessagesState

class AgentState(MessagesState):
    question: str
    context: str
    answer: str
    retry_num: int

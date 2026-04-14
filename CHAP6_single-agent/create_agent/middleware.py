from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

from tools import tools

load_dotenv()


# ===== 모델 정의 =====
basic_model = ChatOpenAI(model="gpt-4o-mini") # [ 1 ]
advanced_model = ChatOpenAI(model="gpt-4o")


# ===== 미들웨어 정의 =====
@wrap_model_call # [ 2 ]
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    """대화 복잡도에 따라 모델을 동적으로 선택하는 미들웨어"""
    message_count = len(request.state["messages"])
    print(f"현재 대화 메시지 수: {message_count}")

    if message_count > 10:
        model = advanced_model
        print("복잡한 대화 감지: 고급 모델(gpt-4o) 사용")
    else:
        model = basic_model

    return handler(request.override(model=model)) # [ 3 ]


# ===== 에이전트 생성 =====
agent = create_agent( # [ 4 ]
    model=basic_model,
    tools=tools,
    middleware=[dynamic_model_selection]
)


if __name__ == "__main__":
    from pathlib import Path
    from langgraph.checkpoint.memory import MemorySaver

    # 그래프 이미지 저장
    save_path = Path(__file__).parent / "middleware_wrap_model_call.png"
    graph_image = agent.get_graph().draw_mermaid_png()
    with open(save_path, "wb") as f:
        f.write(graph_image)

    # 멀티턴 대화를 위한 메모리 체크포인터 설정
    agent_with_memory = create_agent(
        model=basic_model,
        tools=tools,
        middleware=[dynamic_model_selection],
        checkpointer=MemorySaver()
    )

    # 동일한 thread_id로 여러 번 대화하여 메시지 누적
    config = {"configurable": {"thread_id": "test-thread"}}

    # 여러 턴의 대화 시뮬레이션
    questions = [
        "15와 7을 더해주세요.",
        "결과에 3을 곱해주세요.",
        "그 결과에서 10을 빼주세요.",
        "100을 5로 나눠주세요.",
        "25와 25를 더해주세요.",
        "1000에서 500을 빼주세요.",  # 이 시점에서 메시지 10개 초과 예상
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{'='*50}")
        print(f"🔄 턴 {i}: {question}")
        print('='*50)

        response = agent_with_memory.invoke(
            {"messages": [question]},
            config=config
        )

        # 마지막 AI 응답만 출력
        print(f"🤖 응답: {response['messages'][-1].content}")

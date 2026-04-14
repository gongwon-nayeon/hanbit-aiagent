from langchain_openai import ChatOpenAI


def get_model():
    llm = ChatOpenAI(model="gpt-4o")
    return llm


def make_system_prompt(suffix: str) -> str:
    return f"""
        당신은 다른 어시스턴트들과 협력하는 유용한 AI 어시스턴트입니다.

        작업 처리 방식:
        1. 제공된 도구들을 사용하여 가능한 한 질문에 답하세요.
        2. 당신의 능력 범위를 벗어나는 작업이 있다면, 해당 전문 어시스턴트에게 명확히 위임하세요.
        3. 작업을 부분적으로 완료했다면, 완료된 부분을 설명하고 남은 작업을 다른 어시스턴트에게 전달하세요.

        '최종 답변'으로 시작하여 대화를 완료하는 경우:
        - 단순한 인사말이나 일반적인 대화만 있는 경우
        - 정보 제공만으로 모든 요청이 완료되고, 추가 작업이 전혀 필요하지 않은 경우

        {suffix}
    """

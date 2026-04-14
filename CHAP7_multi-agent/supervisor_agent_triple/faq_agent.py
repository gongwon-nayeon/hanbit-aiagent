from langchain.tools import tool
from langchain.agents import create_agent
from langgraph.graph import END

from settings import get_model

@tool
def get_vacation_policy() -> str: # [ 1 ]
    """휴가 정책 정보를 제공합니다."""
    return """
    **휴가 정책**
    1. 연차 휴가: 입사 1년 후 15일 부여
    2. 신청 방법: 사내 시스템을 통해 최소 3일 전 신청
    3. 승인 절차: 직속 상관 승인 후 HR 팀 최종 승인
    4. 긴급 휴가: 경조사, 병가 등은 당일 신청 가능
    """


@tool
def get_work_hours_info() -> str:
    """근무 시간 정보를 제공합니다."""
    return """
    **근무 시간**
    - 정규 근무: 오전 9시 ~ 오후 6시 (점심시간 12-1시)
    - 유연 근무: 오전 8-10시 출근, 9시간 근무
    - 재택 근무: 주 2일까지 가능 (사전 승인 필요)
    - 초과 근무: 사전 승인 시 수당 지급
    """


@tool
def get_benefits_info() -> str:
    """복리후생 정보를 제공합니다."""
    return """
    **복리후생**
    - 4대 보험: 건강보험, 국민연금, 고용보험, 산재보험
    - 퇴직연금: DC형 퇴직연금
    - 건강검진: 연 1회 종합검진 지원
    - 교육비: 업무 관련 교육비 연 100만원 지원
    - 경조사비: 결혼, 출산, 상례 등 지원
    """


@tool
def get_contact_info() -> str:
    """부서별 연락처 정보를 제공합니다. 인사팀, IT팀, 재무팀, 대표번호 등의 연락처를 확인할 수 있습니다."""
    return """
    **부서별 연락처**
    - 인사팀: 02-1234-5678, hr@company.com
    - IT팀: 02-1234-5679, it@company.com
    - 재무팀: 02-1234-5680, finance@company.com
    - 대표번호: 02-1234-5600, info@company.com
    """


model = get_model(model_name="gpt-4o")
tools = [get_vacation_policy, get_work_hours_info, get_benefits_info, get_contact_info]

faq_agent = create_agent( # [ 2 ]
    model=model,
    tools=tools,
    system_prompt="""
    당신은 자주 묻는 질문에 대한 답변을 제공하는 사내 FAQ 에이전트입니다.

    **사용자 질문을 분석하여 적절한 도구를 호출해 답변을 제공하세요:**

    1. **휴가 관련 질문** (연차, 휴가 신청, 휴가 정책 등)
       → get_vacation_policy 도구 사용

    2. **근무 시간 관련 질문** (출퇴근 시간, 재택근무, 유연근무, 초과근무 등)
       → get_work_hours_info 도구 사용

    3. **복리후생 관련 질문** (보험, 퇴직연금, 건강검진, 교육비, 경조사비 등)
       → get_benefits_info 도구 사용

    4. **연락처 관련 질문** (부서 전화번호, 이메일, 인사팀, IT팀, 재무팀 등)
       → get_contact_info 도구 사용

    **중요:**
    - 도구를 호출한 후 결과를 그대로 사용자에게 전달하세요
    - 정보가 없다고 말하지 말고, 반드시 적절한 도구를 먼저 사용해보세요
    - 도구 호출 결과를 기반으로 정확하고 친절하게 답변하세요
    """
)

from langgraph.types import Command
from langchain.messages import HumanMessage
from handoff_tools import create_handoff_messages
from settings import AgentState


def create_faq_agent(state: AgentState) -> Command:
    query = state.get("query", "")
    agent_state = {"messages": [HumanMessage(content=query)]}

    result = faq_agent.invoke(agent_state)

    ai_message, tool_message = create_handoff_messages("faq")

    result["messages"].extend([ai_message, tool_message])

    return Command(
        update={"messages": result["messages"]},
        goto=END,
    )

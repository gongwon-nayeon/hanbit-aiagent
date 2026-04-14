from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from typing import AsyncIterator, Dict, Any, Literal
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
load_dotenv(dotenv_path="../../.env")


class ResponseFormat(BaseModel): # [ 1 ]
    """
    LLM이 따라야 할 응답 포맷
    """
    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str


@tool
def calculator(expression: str) -> str: # [ 2 ]
    """수학 계산을 수행합니다.

    Args:
        expression (str): 계산할 수학 표현식 (예: "2 + 2")

    Returns:
        str: 계산 결과 또는 오류 메시지
    """
    try:
        result = eval(expression)
        return f"계산 결과: {result}"
    except Exception as e:
        return f"계산 오류: {str(e)}"


@tool
def get_current_info() -> str: # [ 3 ]
    """현재 날짜, 시간 등의 정보를 제공합니다.

    Returns:
        str: 요청된 정보
    """
    from datetime import datetime
    now = datetime.now()
    return f"현재 시각: {now.strftime('%Y년 %m월 %d일 %H시 %M분')}"


class LangGraphAgent: # [ 4 ]
    SYSTEM_INSTRUCTION = (
        "당신은 도움이 되는 AI 어시스턴트입니다. "
        "사용자의 질문에 답변하고, 필요한 경우 도구를 사용하세요."
    )

    def __init__(self):
        """에이전트 초기화"""
        self.llm = ChatOpenAI( # [ 5 ]
            model='gpt-4o'
        )

        self.tools = [calculator, get_current_info]

        self.memory = InMemorySaver()

        self.agent = create_agent( # [ 6 ]
            self.llm,
            tools=self.tools,
            system_prompt=self.SYSTEM_INSTRUCTION,
            checkpointer=self.memory,
            response_format=ResponseFormat,
        )

    async def stream( # [ 1 ]
        self,
        query: str,
        session_id: str = "default"
    ) -> AsyncIterator[Dict[str, Any]]:
        inputs = {'messages': [('user', query)]}
        config = {'configurable': {'thread_id': session_id}}

        try: # [ 2 ]
            async for item in self.agent.astream(inputs, config, stream_mode='values'):
                if 'messages' in item:
                    message = item['messages'][-1]

                    if ( # [ 3 ]
                        isinstance(message, AIMessage)
                        and message.tool_calls
                        and len(message.tool_calls) > 0
                    ):
                        yield {
                            'is_task_complete': False,
                            'require_user_input': False,
                            'content': '도구를 실행하는 중...',
                        }

                    elif isinstance(message, ToolMessage): # [ 4 ]
                        yield {
                            'is_task_complete': False,
                            'require_user_input': False,
                            'content': message.content,
                        }

            yield self.get_agent_response(config) # [ 5 ]

        except Exception as e:
            yield {
                'is_task_complete': False,
                'require_user_input': False,
                'content': f"에러 발생: {str(e)}",
            }

    def get_agent_response(self, config):
        current_state = self.agent.get_state(config) # [ 1 ]
        structured_response = current_state.values.get('structured_response')

        if structured_response and isinstance(structured_response, ResponseFormat): # [ 2 ]
            if structured_response.status in ('input_required', 'error'):
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'completed': # [ 3 ]
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': structured_response.message,
                }

        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': (
                '요청을 처리할 수 없습니다. '
                '다시 시도해주세요.'
            ),
        }

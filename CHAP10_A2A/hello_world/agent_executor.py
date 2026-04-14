from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message


class HelloWorldAgent:
    """
    간단한 Hello World 에이전트

    이 에이전트는 항상 "Hello World!"를 반환합니다.
    """

    async def invoke(self) -> str:
        """
        에이전트 실행 메서드

        Returns:
            str: "Hello World!" 메시지
        """
        return "Hello World! 안녕하세요, A2A 에이전트입니다!"


class HelloWorldAgentExecutor(AgentExecutor):
    """
    A2A 프로토콜에 맞는 에이전트 실행자

    AgentExecutor 인터페이스를 구현하여 A2A 서버와 통신합니다.
    """

    def __init__(self):
        """에이전트 인스턴스 초기화"""
        self.agent = HelloWorldAgent()

    async def execute( # [ 1 ]
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        에이전트를 실행하고 결과를 이벤트 큐에 전송

        Args:
            context: 요청 컨텍스트 (사용자 메시지, 세션 정보 등)
            event_queue: 결과를 전송할 이벤트 큐
        """
        result = await self.agent.invoke() # [ 2 ]

        # 결과를 텍스트 메시지로 변환하여 이벤트 큐에 전송
        await event_queue.enqueue_event(new_agent_text_message(result)) # [ 3 ]

    async def cancel( # [ 4 ]
        self,
        context: RequestContext,
        event_queue: EventQueue
    ) -> None:
        """
        작업 취소 메서드

        이 간단한 예제에서는 취소 기능을 지원하지 않습니다.
        """
        raise Exception("cancel은 지원되지 않습니다")

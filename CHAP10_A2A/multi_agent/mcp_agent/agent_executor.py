from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, Part, TextPart
from a2a.utils import new_agent_text_message, new_task
from agent import MCPAgent


class MCPAgentExecutor(AgentExecutor): # [ 1 ]
    """
    MCP 에이전트 실행자

    A2A 프로토콜에 맞춰 MCP 에이전트를 실행합니다.
    """

    def __init__(self):
        """에이전트 인스턴스 초기화"""
        self.agent = MCPAgent()
        self.initialized = False

    async def execute( # [ 2 ]
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
        if not self.initialized:
            try:
                await self.agent.initialize()
                self.initialized = True
            except Exception as e:
                print(f"MCP 에이전트 초기화 실패: {e}")
                # 초기화 실패해도 계속 진행 (OpenAI만 사용)

        # 사용자 입력 가져오기
        query = context.get_user_input()

        # 태스크 생성
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        # 태스크 업데이터
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            # 에이전트 실행 및 스트리밍
            async for item in self.agent.stream(query): # [ 1 ]
                is_complete = item.get('is_task_complete', False)
                require_input = item.get('require_user_input', False)
                content = item.get('content', '')

                if not is_complete and not require_input and content:
                    # 작업 중 - 상태 업데이트
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            content,
                            task.context_id,
                            task.id,
                        ),
                    )
                elif require_input: # [ 2 ]
                    # 사용자 입력 필요
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(
                            content,
                            task.context_id,
                            task.id,
                        ),
                        final=True,
                    )
                    break
                elif is_complete: # [ 3 ]
                    await updater.add_artifact(
                        parts=[Part(root=TextPart(text=content))],
                        name='agent_result'
                    )
                    await updater.complete()
                    break

        except Exception as e:
            # 에러 발생
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f"에러 발생: {str(e)}",
                    task.context_id,
                    task.id,
                ),
            )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue
    ) -> None:
        """
        작업 취소 메서드

        실행 중인 MCP 에이전트 태스크를 취소하고 상태를 canceled로 업데이트합니다.
        """
        task = context.current_task

        # TaskUpdater를 사용하여 취소 상태로 업데이트
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        await updater.cancel(
            new_agent_text_message(
                "MCP 에이전트 작업이 취소되었습니다.",
                task.context_id,
                task.id,
            )
        )

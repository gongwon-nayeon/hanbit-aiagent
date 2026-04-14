import logging
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, Part, TextPart
from a2a.utils import new_agent_text_message, new_task
from agent import WebResearchAgent

logger = logging.getLogger(__name__)


class WebResearchAgentExecutor(AgentExecutor):
    """
    Web Research 에이전트 실행자
    """

    def __init__(self):
        self.agent = WebResearchAgent()
        self.initialized = False

    async def execute( # [ 1 ]
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """에이전트 실행"""
        if not self.initialized:
            try:
                await self.agent.initialize()
                self.initialized = True
                logger.info("[WEB AGENT] [EXECUTOR] 초기화 완료")
            except Exception as e:
                logger.error(f"[WEB AGENT] [ERROR] 초기화 실패: {e}")
                raise

        query = context.get_user_input()
        logger.info(f"[WEB AGENT] [EXECUTOR] 쿼리 수신: {query[:100]}...")

        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            async for item in self.agent.stream(query): # [ 2 ]
                is_complete = item.get('is_task_complete', False)
                require_input = item.get('require_user_input', False)
                content = item.get('content', '')

                if not is_complete and not require_input:
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            content,
                            task.context_id,
                            task.id,
                        ),
                    )
                elif require_input:
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
                        name='web_search_result'
                    )
                    await updater.complete()
                    break

        except Exception as e:
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f"오류 발생: {str(e)}",
                    task.context_id,
                    task.id,
                ),
            )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue
    ) -> None:
        """작업 취소"""
        task = context.current_task
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        await updater.cancel(
            new_agent_text_message(
                "웹 검색 작업이 취소되었습니다.",
                task.context_id,
                task.id,
            )
        )

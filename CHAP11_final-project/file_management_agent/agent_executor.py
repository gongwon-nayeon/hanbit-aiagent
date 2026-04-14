import logging
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, Part, TextPart, DataPart
from a2a.utils import new_agent_text_message, new_task
from agent import FileManagementAgent

logger = logging.getLogger(__name__)


class FileManagementAgentExecutor(AgentExecutor):
    """
    File Management 에이전트 실행자
    """

    def __init__(self):
        self.agent = FileManagementAgent()
        self.initialized = False

    async def execute( # [ 1 ]
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        if not self.initialized:
            try:
                await self.agent.initialize()
                self.initialized = True
                logger.info("[FILE AGENT] [EXECUTOR] 초기화 완료")
            except Exception as e:
                logger.error(f"[FILE AGENT] [ERROR] 초기화 실패: {e}")
                raise

        query = context.get_user_input() # [ 2 ]
        logger.info(f"[FILE AGENT] [EXECUTOR] 쿼리 수신: {query[:100]}...")

        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            async for item in self.agent.stream(query): # [ 3 ]
                is_complete = item.get('is_task_complete', False)
                require_input = item.get('require_user_input', False)
                content = item.get('content', '')

                if not is_complete and not require_input: # [ 4 ]
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
                elif is_complete:
                    data = item.get('data') # [ 5 ]

                    if data and 'files' in data:
                        await updater.add_artifact(
                            parts=[Part(root=DataPart(data=data))],
                            name='file_list'
                        )
                        logger.info(f"[FILE AGENT] [EXECUTOR] 파일 목록 DataPart 추가: {len(data.get('files', []))}개")

                    await updater.add_artifact(
                        parts=[Part(root=TextPart(text=content))],
                        name='file_operation_result'
                    )

                    await updater.complete()
                    break

        except Exception as e:
            await updater.update_status( # [ 6 ]
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
                "파일 작업이 취소되었습니다.",
                task.context_id,
                task.id,
            )
        )

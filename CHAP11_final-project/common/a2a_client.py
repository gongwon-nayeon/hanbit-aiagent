import asyncio
import json
import logging
from uuid import uuid4
from typing import Optional, Dict, Any, List
import httpx

logger = logging.getLogger(__name__)

from a2a.client import A2AClient, A2ACardResolver
from a2a.types import (
    Message,
    MessageSendParams,
    SendMessageRequest,
    Part,
    TextPart,
    DataPart,
    TaskState,
)

from .schemas import (
    AgentResponse,
    get_artifact_text,
    get_artifact_data,
    get_artifact_file_uri,
)


class A2AClientWrapper:
    """
    A2A 클라이언트 래퍼

    A2A SDK 네이티브 타입을 사용한 에이전트 간 통신을 지원합니다.
    """

    def __init__(self, timeout: float = 120.0):
        self.timeout = timeout
        self.httpx_client: Optional[httpx.AsyncClient] = None
        self.agents: Dict[str, Dict[str, Any]] = {}

    async def initialize(self, agent_urls: Dict[str, str]) -> None:
        """
        에이전트 클라이언트 초기화

        Args:
            agent_urls: 에이전트 이름과 URL 매핑
        """
        self.httpx_client = httpx.AsyncClient(timeout=self.timeout)

        for name, url in agent_urls.items():
            try:
                card_resolver = A2ACardResolver(
                    httpx_client=self.httpx_client,
                    base_url=url,
                )
                agent_card = await card_resolver.get_agent_card()

                client = A2AClient(
                    httpx_client=self.httpx_client,
                    agent_card=agent_card,
                )

                self.agents[name] = {
                    'card': agent_card,
                    'client': client,
                    'url': url,
                }

                logger.info(f"[A2A CLIENT] {name} 에이전트 연결: {agent_card.name}")

            except Exception as e:
                logger.error(f"[A2A CLIENT] [ERROR] {name} 에이전트 연결 실패: {str(e)}")

    async def close(self) -> None:
        """클라이언트 종료"""
        if self.httpx_client:
            await self.httpx_client.aclose()

    async def send_message(
        self,
        agent_name: str,
        message: str,
        blocking: bool = True
    ) -> AgentResponse:
        """
        A2A 메시지를 에이전트에게 전송하고 응답을 받습니다.

        Args:
            agent_name: 대상 에이전트 이름
            message: 전송할 메시지 (텍스트 또는 JSON 문자열)
            blocking: True면 완료까지 대기

        Returns:
            AgentResponse: 에이전트 응답 (artifacts 포함)
        """
        if agent_name not in self.agents:
            available = ", ".join(self.agents.keys())
            return AgentResponse(
                success=False,
                error=f"에이전트 '{agent_name}'를 찾을 수 없습니다. 사용 가능: {available}"
            )

        agent = self.agents[agent_name]
        client = agent['client']

        try:
            # A2A Message 생성
            a2a_message = Message(
                role='user',
                parts=[Part(root=TextPart(text=message))],
                message_id=uuid4().hex,
            )

            request = SendMessageRequest(
                id=uuid4().hex,
                params=MessageSendParams(message=a2a_message),
            )

            # A2A 요청 전송
            response = await asyncio.wait_for(
                client.send_message(request),
                timeout=self.timeout
            )

            # 응답 처리
            result = response.root.result

            # Task 응답인 경우
            if hasattr(result, 'artifacts') and result.artifacts:
                artifacts_data = []
                for artifact in result.artifacts:
                    artifact_dict = {
                        "artifact_id": artifact.artifact_id,
                        "name": artifact.name,
                        "description": artifact.description,
                    }
                    # 텍스트 추출
                    text = get_artifact_text(artifact)
                    if text:
                        artifact_dict["text"] = text
                    # 데이터 추출
                    data = get_artifact_data(artifact)
                    if data:
                        artifact_dict["data"] = data
                    # 파일 URI 추출
                    file_uri = get_artifact_file_uri(artifact)
                    if file_uri:
                        artifact_dict["file_uri"] = file_uri

                    artifacts_data.append(artifact_dict)

                return AgentResponse(
                    success=True,
                    artifacts=artifacts_data,
                    message="태스크 완료"
                )

            # Message 직접 응답인 경우
            if hasattr(result, 'parts') and result.parts:
                texts = []
                for part in result.parts:
                    if hasattr(part, 'root') and hasattr(part.root, 'text'):
                        texts.append(part.root.text)
                    elif hasattr(part, 'text'):
                        texts.append(part.text)

                if texts:
                    response_text = "\n".join(texts)
                    return AgentResponse(
                        success=True,
                        artifacts=[{"name": "response", "text": response_text}],
                        message="응답 완료"
                    )

            return AgentResponse(
                success=False,
                error="응답을 받지 못했습니다"
            )

        except asyncio.TimeoutError:
            return AgentResponse(
                success=False,
                error=f"타임아웃 ({self.timeout}초)"
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e)
            )

    async def send_streaming_message(
        self,
        agent_name: str,
        message: str,
    ):
        """
        A2A 스트리밍 메시지 전송 (비동기 제너레이터)

        Args:
            agent_name: 대상 에이전트 이름
            message: 전송할 메시지

        Yields:
            스트리밍 이벤트 (상태 업데이트, 아티팩트 등)
        """
        if agent_name not in self.agents:
            yield {"error": f"에이전트 '{agent_name}'를 찾을 수 없습니다"}
            return

        agent = self.agents[agent_name]
        client = agent['client']

        try:
            a2a_message = Message(
                role='user',
                parts=[Part(root=TextPart(text=message))],
                message_id=uuid4().hex,
            )

            request = SendMessageRequest(
                id=uuid4().hex,
                params=MessageSendParams(message=a2a_message),
            )

            # 스트리밍 응답 처리
            async for event in client.send_message_streaming(request):
                if hasattr(event, 'root'):
                    event_data = event.root

                    # TaskStatusUpdateEvent
                    if hasattr(event_data, 'status'):
                        yield {
                            "type": "status",
                            "state": event_data.status.state.value if hasattr(event_data.status.state, 'value') else str(event_data.status.state),
                        }

                    # TaskArtifactUpdateEvent
                    elif hasattr(event_data, 'artifact'):
                        artifact = event_data.artifact
                        artifact_dict = {
                            "type": "artifact",
                            "artifact_id": artifact.artifact_id,
                            "name": artifact.name,
                        }
                        text = get_artifact_text(artifact)
                        if text:
                            artifact_dict["text"] = text
                        data = get_artifact_data(artifact)
                        if data:
                            artifact_dict["data"] = data
                        yield artifact_dict

        except Exception as e:
            yield {"error": str(e)}

"""
A2A 공통 스키마 정의

A2A SDK의 네이티브 타입을 재사용하고,
비즈니스 로직에 필요한 인텐트/타입만 별도 정의합니다.

A2A SDK 핵심 타입:
- Task: A2A 태스크 (from a2a.types)
- TaskState: 태스크 상태 (from a2a.types)
- Artifact: 결과물 (from a2a.types)
- Part: 컨텐츠 조각 (from a2a.types)
- TextPart, DataPart, FilePart: Part 유형들 (from a2a.types)
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import uuid4
import json

# A2A SDK 타입 재사용 (re-export)
from a2a.types import (
    Task,
    TaskState,
    TaskStatus,
    Artifact,
    Part,
    TextPart,
    DataPart,
    FilePart,
    FileWithUri,
    FileWithBytes,
    Message,
)
from a2a.utils import new_task, new_agent_text_message


class TaskIntent(str, Enum):
    """태스크 인텐트 유형 - 비즈니스 로직용"""
    # Orchestrator
    ROUTE = "route"
    PLAN = "plan"

    # Web Research Agent
    SEARCH_WEB = "search_web"
    SEARCH_NEWS = "search_news"
    FETCH_URL = "fetch_url"

    # Internal RAG Agent
    INDEX_FILE = "index_file"
    SEARCH_DOCUMENTS = "search_documents"
    ANSWER_QUESTION = "answer_question"
    COMPARE_DOCUMENTS = "compare_documents"

    # File Management Agent
    UPLOAD_FILE = "upload_file"
    DOWNLOAD_FILE = "download_file"
    LIST_FILES = "list_files"
    GET_FILE_INFO = "get_file_info"
    DELETE_FILE = "delete_file"
    CREATE_VERSION = "create_version"


class ArtifactType(str, Enum):
    """아티팩트 유형 - 비즈니스 로직용"""
    # 파일 관련
    FILE_METADATA = "file_metadata"
    FILE_CONTENT = "file_content"
    FILE_LIST = "file_list"

    # 검색 결과
    SEARCH_RESULT_SET = "search_result_set"
    WEB_PAGE_SUMMARY = "web_page_summary"

    # RAG 관련
    RETRIEVED_CHUNK_SET = "retrieved_chunk_set"
    RAG_ANSWER = "rag_answer"
    DOCUMENT_SUMMARY = "document_summary"

    # 계획/실행
    PLAN = "plan"
    EXECUTION_RESULT = "execution_result"

    # 오류
    ERROR = "error"


def create_text_artifact(
    name: str,
    text: str,
    description: Optional[str] = None,
    artifact_type: Optional[ArtifactType] = None,
) -> Artifact:
    """
    텍스트 기반 아티팩트 생성 헬퍼

    A2A SDK의 Artifact를 쉽게 생성할 수 있도록 지원합니다.
    """
    metadata = {}
    if artifact_type:
        metadata["artifact_type"] = artifact_type.value

    return Artifact(
        artifact_id=uuid4().hex,
        name=name,
        description=description,
        parts=[Part(root=TextPart(text=text))],
        metadata=metadata if metadata else None,
    )


def create_data_artifact(
    name: str,
    data: Dict[str, Any],
    description: Optional[str] = None,
    artifact_type: Optional[ArtifactType] = None,
) -> Artifact:
    """
    구조화된 데이터 아티팩트 생성 헬퍼

    JSON 직렬화 가능한 데이터를 A2A Artifact로 변환합니다.
    """
    metadata = {}
    if artifact_type:
        metadata["artifact_type"] = artifact_type.value

    return Artifact(
        artifact_id=uuid4().hex,
        name=name,
        description=description,
        parts=[Part(root=DataPart(data=data))],
        metadata=metadata if metadata else None,
    )


def create_file_artifact(
    name: str,
    file_uri: str,
    media_type: str = "application/octet-stream",
    file_name: Optional[str] = None,
    description: Optional[str] = None,
    artifact_type: Optional[ArtifactType] = None,
) -> Artifact:
    """
    파일 참조 아티팩트 생성 헬퍼 (URI 방식)

    파일 URI (예: gdrive://file/{FILE_ID})를 포함한 아티팩트를 생성합니다.
    다른 에이전트가 이 URI를 통해 파일에 접근할 수 있습니다.
    """
    metadata = {}
    if artifact_type:
        metadata["artifact_type"] = artifact_type.value

    return Artifact(
        artifact_id=uuid4().hex,
        name=name,
        description=description,
        parts=[Part(root=FilePart(
            file=FileWithUri(
                uri=file_uri,
                mimeType=media_type,
                name=file_name or name,
            )
        ))],
        metadata=metadata if metadata else None,
    )


def create_file_bytes_artifact(
    name: str,
    file_bytes: bytes,
    media_type: str = "application/octet-stream",
    file_name: Optional[str] = None,
    description: Optional[str] = None,
    artifact_type: Optional[ArtifactType] = None,
) -> Artifact:
    """
    파일 내용 아티팩트 생성 헬퍼 (Bytes 방식)

    파일 내용을 base64 인코딩하여 아티팩트에 직접 포함합니다.
    작은 파일을 에이전트 간 직접 전달할 때 사용합니다.
    """
    import base64

    metadata = {}
    if artifact_type:
        metadata["artifact_type"] = artifact_type.value

    # bytes를 base64 문자열로 인코딩
    file_content_b64 = base64.b64encode(file_bytes).decode('utf-8')

    return Artifact(
        artifact_id=uuid4().hex,
        name=name,
        description=description,
        parts=[Part(root=FilePart(
            file=FileWithBytes(
                bytes=file_content_b64,
                mimeType=media_type,
                name=file_name or name,
            )
        ))],
        metadata=metadata if metadata else None,
    )


def get_artifact_text(artifact: Artifact) -> Optional[str]:
    """아티팩트에서 텍스트 추출"""
    if artifact.parts:
        for part in artifact.parts:
            if hasattr(part, 'root') and isinstance(part.root, TextPart):
                return part.root.text
            elif hasattr(part, 'text') and part.text:
                return part.text
    return None


def get_artifact_data(artifact: Artifact) -> Optional[Dict[str, Any]]:
    """아티팩트에서 데이터 추출"""
    if artifact.parts:
        for part in artifact.parts:
            if hasattr(part, 'root') and isinstance(part.root, DataPart):
                return part.root.data
            elif hasattr(part, 'data') and part.data:
                return part.data.data if hasattr(part.data, 'data') else part.data
    return None


def get_artifact_file_uri(artifact: Artifact) -> Optional[str]:
    """아티팩트에서 파일 URI 추출 (FileWithUri 방식)"""
    if artifact.parts:
        for part in artifact.parts:
            if hasattr(part, 'root') and isinstance(part.root, FilePart):
                file_obj = part.root.file
                if hasattr(file_obj, 'uri'):  # FileWithUri
                    return file_obj.uri
            elif hasattr(part, 'file') and part.file:
                if hasattr(part.file, 'uri'):  # FileWithUri
                    return part.file.uri
    return None


def get_artifact_file_bytes(artifact: Artifact) -> Optional[bytes]:
    """아티팩트에서 파일 내용 추출 (FileWithBytes 방식)"""
    import base64

    if artifact.parts:
        for part in artifact.parts:
            if hasattr(part, 'root') and isinstance(part.root, FilePart):
                file_obj = part.root.file
                if hasattr(file_obj, 'bytes'):  # FileWithBytes
                    return base64.b64decode(file_obj.bytes)
            elif hasattr(part, 'file') and part.file:
                if hasattr(part.file, 'bytes'):  # FileWithBytes
                    return base64.b64decode(part.file.bytes)
    return None


class AgentContext(BaseModel):
    """에이전트 컨텍스트 - 비즈니스 로직용 확장 메타데이터"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# A2A Client 호출을 위한 요청/응답 래퍼
class AgentRequest(BaseModel):
    """에이전트 요청 래퍼"""
    intent: TaskIntent
    input_data: Dict[str, Any] = Field(default_factory=dict)
    context: AgentContext = Field(default_factory=AgentContext)

    def to_message_text(self) -> str:
        """A2A 메시지로 변환할 텍스트 생성"""
        return json.dumps({
            "intent": self.intent.value,
            "input": self.input_data,
            "context": self.context.model_dump(),
        }, ensure_ascii=False)


class AgentResponse(BaseModel):
    """에이전트 응답 래퍼"""
    success: bool = True
    message: Optional[str] = None
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None

    @classmethod
    def from_task(cls, task: Task) -> "AgentResponse":
        """A2A Task에서 응답 생성"""
        artifacts_data = []
        if task.artifacts:
            for artifact in task.artifacts:
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

        is_success = task.status.state in [TaskState.completed]
        error_msg = None
        if task.status.state == TaskState.failed and task.status.message:
            error_msg = get_artifact_text(task.status.message) if hasattr(task.status.message, 'parts') else str(task.status.message)

        return cls(
            success=is_success,
            artifacts=artifacts_data,
            error=error_msg,
        )

import os
import json
import logging
from typing import Dict, Any, AsyncIterator

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool

from gdrive_client import get_gdrive_client

logger = logging.getLogger(__name__)
load_dotenv()

_client = get_gdrive_client()


@tool
def upload_file(content: str, filename: str, mime_type: str = "text/plain", folder_id: str = "") -> str: # [ 1 ]
    """
    Google Drive에 파일을 업로드합니다.

    Args:
        content: 업로드할 파일 내용 (텍스트)
        filename: 저장할 파일명 (예: report.txt)
        mime_type: MIME 타입 (기본값: text/plain)
        folder_id: 저장할 폴더 ID (선택, 비워두면 기본 폴더에 저장)
    """
    try:
        from datetime import datetime
        result = _client.upload_file(
            content=content.encode('utf-8'),
            filename=filename,
            mime_type=mime_type,
            description=f"Uploaded at {datetime.now().isoformat()}",
            parent_folder_id=folder_id if folder_id else None
        )

        return json.dumps({
            "success": True,
            "message": f"파일 '{filename}' 업로드 완료",
            **result
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@tool
def download_file_as_base64(file_id: str) -> str: # [ 2 ]
    """
    Google Drive에서 파일을 다운로드하여 Base64로 인코딩하여 반환합니다.
    RAG Agent에게 전달하여 텍스트 추출 및 인덱싱에 사용합니다.

    Args:
        file_id: 다운로드할 파일 ID 또는 storage_ref

    Returns:
        Base64 인코딩된 파일 내용과 메타데이터
    """
    try:
        result = _client.download_file_as_base64(file_id)
        if result is None:
            return json.dumps({"success": False, "error": "파일을 찾을 수 없습니다"}, ensure_ascii=False)

        return json.dumps({
            "success": True,
            **result
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@tool
def get_file_info(file_id: str) -> str: # [ 1 ]
    """
    Google Drive 파일의 상세 정보를 조회합니다.

    Args:
        file_id: 조회할 파일 ID 또는 storage_ref
    """
    try:
        result = _client.get_file_info(file_id)
        if result is None:
            return json.dumps({"success": False, "error": "파일을 찾을 수 없습니다"}, ensure_ascii=False)

        return json.dumps({
            "success": True,
            "file_info": result
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@tool
def find_folder_by_name(folder_name: str) -> str: # [ 2 ]
    """
    폴더 이름으로 Google Drive에서 폴더를 검색합니다.

    Args:
        folder_name: 검색할 폴더 이름 (예: "보고서", "문서")

    Returns:
        폴더 정보 (folder_id 포함)
    """
    try:
        folders = _client.find_folder_by_name(folder_name)

        if not folders:
            return json.dumps({
                "success": False,
                "error": f"'{folder_name}' 폴더를 찾을 수 없습니다"
            }, ensure_ascii=False)

        return json.dumps({
            "success": True,
            "count": len(folders),
            "folders": folders
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@tool
def list_files(folder_name: str = "", folder_id: str = "", search_query: str = "", max_results: int = 20) -> str: # [ 1 ]
    """
    Google Drive의 파일 목록을 조회합니다.
    폴더 이름, 폴더 ID, 파일명 검색을 모두 지원합니다.

    Args:
        folder_name: 폴더 이름 (예: "보고서") - folder_id가 없을 때 폴더 검색에 사용
        folder_id: 특정 폴더 ID (직접 지정 시 우선 사용, 비워두면 기본 앱 폴더)
        search_query: 파일명 검색어 (선택, 비워두면 전체 조회)
        max_results: 최대 결과 수 (기본값: 20)

    Returns:
        파일 목록 (folder_name, folder_id, files 포함)
    """
    try:
        # folder_id가 없고 folder_name이 있으면 폴더 검색
        target_folder_id = folder_id
        found_folder_name = folder_name or "지정된 폴더"

        if not target_folder_id and folder_name:
            folders = _client.find_folder_by_name(folder_name, max_results=1)
            if not folders:
                return json.dumps({
                    "success": False,
                    "error": f"'{folder_name}' 폴더를 찾을 수 없습니다"
                }, ensure_ascii=False)
            target_folder_id = folders[0]['folder_id']
            found_folder_name = folders[0]['folder_name']
        elif not target_folder_id:
            # 기본 앱 폴더 사용
            target_folder_id = _client.app_folder_id
            found_folder_name = "기본 앱 폴더"

        # 파일 목록 조회
        query = f"name contains '{search_query}'" if search_query else None
        files = _client.list_files(query=query, page_size=max_results, folder_id=target_folder_id)

        return json.dumps({
            "success": True,
            "folder_name": found_folder_name,
            "folder_id": target_folder_id,
            "count": len(files),
            "files": files
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@tool
def delete_file(file_id: str, permanent: bool = False) -> str: # [ 2 ]
    """
    Google Drive에서 파일을 삭제합니다.

    Args:
        file_id: 삭제할 파일 ID 또는 storage_ref
        permanent: 영구 삭제 여부 (기본값: False, 휴지통으로 이동)
    """
    try:
        # 파일명 조회
        info = _client.get_file_info(file_id)
        if info is None:
            return json.dumps({"success": False, "error": "파일을 찾을 수 없습니다"}, ensure_ascii=False)

        filename = info['filename']
        success = _client.delete_file(file_id, permanent=permanent)

        if not success:
            return json.dumps({"success": False, "error": "파일 삭제 실패"}, ensure_ascii=False)

        action = "영구 삭제" if permanent else "휴지통으로 이동"
        return json.dumps({"success": True, "message": f"파일 '{filename}' {action} 완료"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@tool
def update_file(file_id: str, new_content: str = "", new_name: str = "") -> str: # [ 1 ]
    """
    Google Drive 파일을 업데이트합니다.

    Args:
        file_id: 업데이트할 파일 ID 또는 storage_ref
        new_content: 새 파일 내용 (선택)
        new_name: 새 파일명 (선택)
    """
    try:
        content_bytes = new_content.encode('utf-8') if new_content else None
        result = _client.update_file(file_id, content=content_bytes, new_name=new_name)

        return json.dumps({
            "success": True,
            "message": f"파일 '{result['filename']}' 업데이트 완료",
            **result
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@tool
def create_folder(folder_name: str, parent_folder_id: str = "") -> str: # [ 2 ]
    """
    Google Drive에 새 폴더를 생성합니다.

    Args:
        folder_name: 생성할 폴더명
        parent_folder_id: 부모 폴더 ID (선택, 비워두면 기본 앱 폴더에 생성)
    """
    try:
        result = _client.create_folder(folder_name, parent_folder_id=parent_folder_id if parent_folder_id else None)

        return json.dumps({
            "success": True,
            "message": f"폴더 '{folder_name}' 생성 완료",
            **result
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


tools = [
    upload_file,
    download_file_as_base64,
    get_file_info,
    list_files,
    find_folder_by_name,
    delete_file,
    update_file,
    create_folder
]


class FileManagementAgent:
    """A2A 프로토콜용 에이전트 래퍼"""

    def __init__(self, model_name: str = "openai:gpt-4o"): # [ 1 ]
        self.model_name = model_name
        self.graph = None
        self.initialized = False

    async def initialize(self) -> None:
        if self.initialized:
            return
        _client.initialize()
        self.graph = create_agent(model=self.model_name, tools=tools)
        self.initialized = True
        logger.info("[FILE AGENT] [INIT] File Management Agent 초기화 완료")

    async def stream(self, query: str) -> AsyncIterator[Dict[str, Any]]: # [ 2 ]
        if not self.initialized:
            await self.initialize()

        final_message = None
        file_list_data = None  # 파일 목록 데이터

        for chunk in self.graph.stream({"messages": [("user", query)]}):
            for node_name, node_output in chunk.items():
                messages = node_output.get("messages", [])

                for msg in messages:
                    if hasattr(msg, 'tool_calls') and msg.tool_calls: # [ 3 ]
                        tool_names = [tc.get('name', 'unknown') for tc in msg.tool_calls]
                        yield {
                            "is_task_complete": False,
                            "require_user_input": False,
                            "content": f"🔧 도구 실행 중... ({', '.join(tool_names)})"
                        }

                    if hasattr(msg, 'content') and msg.content: # [ 4 ]
                        if not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                            final_message = msg.content
                            try:
                                result = json.loads(msg.content)
                                if result.get("success") and "files" in result:
                                    file_list_data = result
                                    logger.info(f"[FILE AGENT] 파일 목록 발견: {len(result['files'])}개")
                            except (json.JSONDecodeError, TypeError):
                                pass

        yield { # [ 5 ]
            "is_task_complete": True,
            "require_user_input": False,
            "content": final_message if final_message else "응답을 생성하지 못했습니다.",
            "data": file_list_data
        }


if __name__ == "__main__":
    import asyncio

    async def test():
        print("=" * 60)
        print("File Management Agent 테스트")
        print("=" * 60)

        agent = FileManagementAgent()
        query = input("질문을 입력하세요:")

        print(f"\n👤 Query: {query}")
        print("-" * 60)

        async for chunk in agent.stream(query):
            content = chunk.get("content", "")
            is_complete = chunk.get("is_task_complete", False)

            if not is_complete:
                print(f"{content}")
            else:
                print(f"\n💬 {content}")

    asyncio.run(test())

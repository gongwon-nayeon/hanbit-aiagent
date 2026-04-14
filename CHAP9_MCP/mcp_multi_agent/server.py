from mcp.server.fastmcp import FastMCP
import os
import stat
import time
from typing import List


mcp = FastMCP( # [ 1 ]
    "FileSearch",
    instructions="로컬 파일 검색을 도와주는 어시스턴트입니다."
)


# 파일 목록 호출
@mcp.tool() # [ 2 ]
async def file_listup(directory: str) -> List[str]:
    """지정된 디렉토리 경로의 파일 이름 목록을 반환합니다."""
    try:
        return os.listdir(directory)
    except Exception as e:
        return [f"오류: {str(e)}"]


# 파일 검색 요약 및 정리 담당
@mcp.tool() # [ 3 ]
async def file_info(path: str) -> dict:
    """
    지정된 경로의 파일 또는 디렉토리에 대한 상세 정보를 반환합니다.
    """
    if not os.path.exists(path):
        return {"error": f"경로 '{path}' 가 존재하지 않습니다."}

    try:
        stat_info = os.stat(path)

        permissions = stat.filemode(stat_info.st_mode)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "path": os.path.abspath(path),
            "content": content,
            "type": "file",
            "size": stat_info.st_size,  # bytes
            "created_time": time.ctime(stat_info.st_birthtime),
            "modified_time": time.ctime(stat_info.st_mtime),
            "access_time": time.ctime(stat_info.st_atime),
            "permissions": permissions,
        }
    except Exception as e:
        return {"error": str(e)}


# 파일 쓰기 저장 담당
@mcp.tool() # [ 4 ]
async def save_file(content: str, output_path="file_info.md") -> str:
    """제공된 내용을 지정된 output_path의 텍스트 파일에 작성합니다."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


if __name__ == "__main__": # [ 5 ]
    mcp.run(transport="stdio")

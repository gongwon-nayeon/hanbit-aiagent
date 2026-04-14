from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from datetime import datetime
from pathlib import Path


mcp = FastMCP("MCPServer") # [ 1 ]


@mcp.tool() # [ 2 ]
def read_user_info() -> str:
    """
    사용자의 정보를 담고 있는 txt 파일을 읽어옵니다.

    Returns:
        str: my_info.txt 파일의 내용
    """
    info_file_path = Path(__file__).parent / "my_info.txt" # [ 3 ]

    try:
        with open(info_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return "my_info.txt 파일을 찾을 수 없습니다."
    except Exception as e:
        return f"파일을 읽는 중 오류가 발생했습니다: {str(e)}"

@mcp.tool()
def save_diary(conversation_summary: str, emotion: str, resolution: str) -> dict:
    """
    일기 형태로 텍스트 파일을 저장합니다. 모든 내용은 한국어로 작성합니다.

    Args:
        conversation_summary (str): 오늘의 대화 내용
        emotion (str): 오늘의 감정
        resolution (str): 오늘의 다짐

    Returns:
        dict: 저장 결과 (저장 경로, 파일명, 성공 여부)
    """ # [ 1 ]
    try:
        diary_dir = Path(__file__).parent / "diary" # [ 2 ]
        diary_dir.mkdir(exist_ok=True)

        # 파일명은 날짜_시간으로 자동 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") # [ 3 ]
        filename = f"diary_{timestamp}.txt"
        file_path = diary_dir / filename

        # 날짜와 시간 정보
        timestamp_str = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분") # [ 4 ]

        # 일기 형식으로 내용 구성
        full_content = f"""[{timestamp_str}]

📝 오늘의 대화 내용
{conversation_summary}

💭 오늘의 감정
{emotion}

✨ 오늘의 다짐
{resolution}
"""

        # 파일 저장
        with open(file_path, "w", encoding="utf-8") as f: # [ 5 ]
            f.write(full_content)

        return {
            "success": True,
            "path": str(file_path.absolute()),
            "filename": filename,
            "message": f"일기가 성공적으로 저장되었습니다."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"파일 저장 중 오류가 발생했습니다: {str(e)}"
        }

@mcp.prompt()
def default_prompt(message: str) -> list[base.Message]:
    return [
        base.AssistantMessage(
            "당신은 따뜻하고 공감 능력이 뛰어난 개인 비서입니다. \n"
            "- 사용자가 오늘 있었던 일을 편하게 이야기할 수 있도록 경청하고 공감해주세요\n"
            "- 대화가 자연스럽게 이어지도록 적절한 질문을 던져주세요\n"
            "- 사용자의 감정을 이해하고 긍정적인 피드백을 제공해주세요\n"
            "- 사용자가 대화를 끝내려 하면, 지금까지의 대화 내용을 담아 일기를 작성하세요\n"
            "- 존댓말을 사용하되, 친근하고 편안한 말투를 사용하세요"
        ),
        base.UserMessage(message),
    ]

if __name__ == "__main__":
    mcp.run(transport="stdio")

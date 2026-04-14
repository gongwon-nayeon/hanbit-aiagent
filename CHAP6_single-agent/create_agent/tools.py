from langchain.tools import tool


@tool
def calculator(a: int, b: int, operation: str) -> str:
    """
    간단한 계산기 도구입니다.

    Args:
        a: 첫 번째 숫자
        b: 두 번째 숫자
        operation: 연산 종류 (add, subtract, multiply, divide)
    """
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        result = a / b if b != 0 else "0으로 나눌 수 없습니다"
    else:
        return f"지원하지 않는 연산: {operation}"

    return f"{a} {operation} {b} = {result}"


# 도구 목록
tools = [calculator]

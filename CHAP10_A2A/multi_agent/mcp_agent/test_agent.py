import asyncio
import sys
from agent import MCPAgent


async def main():
    """테스트 메인 함수"""
    print("=" * 60)
    print("MCP 에이전트 테스트")
    print("=" * 60)

    # 에이전트 생성
    agent = MCPAgent()

    # 초기화
    print("\n에이전트 초기화 중...")
    await agent.initialize()

    # 테스트 질문들
    test_queries = [
        "2025년 AI 에이전트 트렌드는?",
        "파이썬의 최신 버전은?",
        "MCP 프로토콜이란 무엇인가?",
    ]

    print("\n" + "=" * 60)
    print("테스트 질문 실행")
    print("=" * 60 + "\n")

    for i, query in enumerate(test_queries, 1):
        print(f"\n[질문 {i}] {query}")
        print("-" * 60)

        try:
            async for response in agent.stream(query):
                content = response.get("content", "")
                is_complete = response.get("is_task_complete", False)

                if content:
                    print(content)

                if is_complete:
                    print("-" * 60)
                    break

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    # Windows 이벤트 루프 정책 설정
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()

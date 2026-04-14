import asyncio
import sys
from agent import LangGraphAgent


async def main():
    agent = LangGraphAgent()

    test_queries = [
        "25 곱하기 4는?",
        "현재 시간이 몇 시인가요?",
        "100을 3으로 나누면 얼마인가요?",
    ]
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
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
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

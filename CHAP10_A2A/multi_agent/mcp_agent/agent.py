from typing import AsyncIterator, Dict, Any, List, Optional
from dotenv import load_dotenv
import os
import json
from openai import AsyncOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from contextlib import asynccontextmanager

load_dotenv()
load_dotenv(dotenv_path="../../.env")


class MCPAgent: # [ 1 ]
    def __init__(self):
        """에이전트 초기화"""
        self.mcp_url = None
        self.tools = []
        self.initialized = False
        self.openai_client = None
        self._current_session: Optional[ClientSession] = None
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    @asynccontextmanager
    async def _get_mcp_session(self): # [ 2 ]
        """MCP 세션을 Context Manager로 관리"""
        async with streamablehttp_client(self.mcp_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    async def initialize(self): # [ 3 ]
        if self.initialized:
            return

        try:
            self.mcp_url = f"https://mcp.tavily.com/mcp/?tavilyApiKey={self.tavily_api_key}"
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)

            async with self._get_mcp_session() as session:
                tools_result = await session.list_tools()
                self.tools = tools_result.tools

                for tool in self.tools:
                    print(f"  - {tool.name}: {tool.description or ''}")

            self.initialized = True

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str: # [ 1 ]
        """
        MCP 도구를 실행합니다.

        Args:
            tool_name: 도구 이름
            parameters: 도구 파라미터

        Returns:
            str: 도구 실행 결과
        """
        try:
            # print(f"\n도구 실행: {tool_name}")
            # print(f"   인자: {json.dumps(parameters, ensure_ascii=False, indent=2)}")

            # 새 세션으로 도구 실행
            async with self._get_mcp_session() as session: # [ 2 ]
                result = await session.call_tool(tool_name, arguments=parameters)

                # 결과에서 텍스트 추출
                if result.content: # [ 3 ]
                    for item in result.content:
                        if hasattr(item, 'text'):
                            # print("도구 실행 성공")
                            return item.text
                    # text 속성이 없으면 전체 내용 반환
                    return str(result.content[0])

                return "도구 실행 완료 (결과 없음)"

        except Exception as e:
            return f"도구 실행 중 오류 발생: {str(e)}"


    async def process_query(self, query: str) -> AsyncIterator[Dict[str, Any]]:
        """
        사용자 쿼리를 처리합니다.
        OpenAI를 사용하여 사용자 의도를 파악하고 적절한 도구를 호출합니다.

        Args:
            query: 사용자 질문

        Yields:
            Dict: 에이전트 응답
        """
        if not self.initialized:
            await self.initialize()

        try:
            tools_for_openai = [] # [ 1 ]
            for tool in self.tools:
                tool_schema = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema or {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }
                tools_for_openai.append(tool_schema)

            # OpenAI API 호출
            messages = [ # [ 2 ]
                {
                    "role": "system",
                    "content": "당신은 웹 검색을 수행할 수 있는 유용한 어시스턴트입니다. 사용자의 질문에 답하기 위해 필요하다면 tavily_search 도구를 사용하세요."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]

            yield {
                "is_task_complete": False,
                "require_user_input": False,
                "content": "질문을 분석하고 있습니다...",
            }

            response = await self.openai_client.chat.completions.create( # [ 3 ]
                model="gpt-4o-mini",
                messages=messages,
                tools=tools_for_openai,
                tool_choice="auto"
            )

            response_message = response.choices[0].message

            if response_message.tool_calls: # [ 1 ]
                for tool_call in response_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    yield {
                        "is_task_complete": False,
                        "require_user_input": False,
                        "content": f"도구 실행: {tool_name}\n인자: {json.dumps(tool_args, ensure_ascii=False, indent=2)}",
                    }

                    tool_result = await self.execute_tool(tool_name, tool_args)

                    yield {
                        "is_task_complete": False,
                        "require_user_input": False,
                        "content": f"도구 실행 결과:\n{tool_result[:500]}{'...' if len(tool_result) > 500 else ''}",
                    }

                    messages.append({ # [ 2 ]
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": tool_call.function.arguments
                                }
                            }
                        ]
                    })

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })

                final_response = await self.openai_client.chat.completions.create( # [ 3 ]
                    model="gpt-4o-mini",
                    messages=messages
                )

                final_content = final_response.choices[0].message.content

                yield {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": f"최종 답변:\n{final_content}",
                }
            else: # [ 4 ]
                yield {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": response_message.content,
                }

        except Exception as e:
            yield {
                "is_task_complete": False,
                "require_user_input": False,
                "content": f"에러 발생: {str(e)}",
            }

    async def stream(
        self,
        query: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        에이전트를 실행하고 결과를 스트리밍합니다.

        Args:
            query: 사용자 질문

        Yields:
            Dict: 에이전트 응답
        """
        async for response in self.process_query(query):
            yield response

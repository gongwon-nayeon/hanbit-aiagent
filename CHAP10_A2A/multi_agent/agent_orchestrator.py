import asyncio
from uuid import uuid4
import os
import json
import httpx
from dotenv import load_dotenv

from a2a.client import A2AClient
from a2a.types import (
    Message,
    MessageSendParams,
    SendMessageRequest,
    TextPart,
)
from a2a.client import A2ACardResolver

from openai import AsyncOpenAI

load_dotenv(dotenv_path="../.env")


class AgentOrchestrator:
    def __init__(self, agent_urls: dict): # [ 1 ]
        """
        오케스트레이터 초기화

        Args:
            agent_urls: 에이전트 이름과 URL 매핑
                예: {'langgraph': 'http://localhost:10001', 'mcp': 'http://localhost:10002'}
        """
        self.agent_urls = agent_urls
        self.agents = {}  # A2A 클라이언트 저장소
        self.httpx_client = None
        self.openai_client = None  # OpenAI 클라이언트
        self.conversation_history = []  # 대화 이력 저장

    async def initialize(self): # [ 2 ]
        """
        에이전트 초기화

        1. 각 에이전트의 AgentCard 가져오기
        2. A2A 클라이언트 생성
        3. OpenAI 클라이언트 생성
        """
        self.httpx_client = httpx.AsyncClient(timeout=60.0)

        for name, url in self.agent_urls.items(): # [ 3 ]
            try:
                card_resolver = A2ACardResolver(
                    httpx_client=self.httpx_client,
                    base_url=url,
                )
                agent_card = await card_resolver.get_agent_card()

                client = A2AClient( # [ 4 ]
                    httpx_client=self.httpx_client,
                    agent_card=agent_card,
                )

                self.agents[name] = {
                    'card': agent_card,
                    'client': client,
                    'url': url,
                }

                print(f"{name} 에이전트: {agent_card.name}")

            except Exception as e:
                print(f"{name} 에이전트 초기화 실패: {str(e)}")

        api_key = os.getenv('OPENAI_API_KEY') # [ 5 ]
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다")

        self.openai_client = AsyncOpenAI(api_key=api_key)

    async def _call_agent(self, agent_name: str, task: str) -> str:
        """
        실제로 A2A 프로토콜을 통해 에이전트를 호출하는 내부 메서드

        Args:
            agent_name: 호출할 에이전트 이름
            task: 작업 내용

        Returns:
            str: 에이전트의 응답
        """
        if agent_name not in self.agents: # [ 1 ]
            available = ", ".join(self.agents.keys())
            return f"에러: '{agent_name}' 에이전트를 찾을 수 없습니다. 사용 가능한 에이전트: {available}"

        agent = self.agents[agent_name] # [ 2 ]
        client = agent['client']

        try:
            # A2A 프로토콜로 메시지 생성
            message = Message( # [ 3 ]
                kind='message',
                role='user',
                parts=[TextPart(kind='text', text=task)],
                message_id=uuid4().hex,
            )

            # 메시지 전송 요청
            request = SendMessageRequest( # [ 4 ]
                id=uuid4().hex,
                params=MessageSendParams(message=message),
            )

            # A2A 클라이언트로 메시지 전송 (타임아웃 60초)
            response = await asyncio.wait_for( # [ 5 ]
                client.send_message(request),
                timeout=60.0
            )

            result = response.root.result # [ 6 ]
            history = result.history
            artifacts = result.artifacts

            if artifacts:
                for artifact in artifacts:
                    if artifact.parts:
                        texts = [p.root.text for p in artifact.parts if hasattr(p.root, 'text')]
                        if texts:
                            return "\n".join(texts)

            return "응답을 받지 못했습니다"

        except Exception as e:
            return f"에러: {str(e)}"

    async def process_query(self, user_query: str) -> str:
        """
        사용자 질문을 처리합니다 (Orchestrator 패턴).

        GPT가 여러 에이전트를 순차적으로 호출하여 복잡한 작업을 처리합니다.

        Args:
            user_query: 사용자 질문

        Returns:
            str: 최종 통합 응답
        """
        print(f"\n💬 사용자 질문: {user_query}")
        print("🤔 Orchestrator가 작업 분석 중...")

        agent_list = [] # [ 1 ]
        for name, agent_info in self.agents.items():
            card = agent_info['card']
            agent_list.append(f"- {name}: {card.description}")

        agents_desc = "\n".join(agent_list)

        # [ 2 ]
        system_message = f"""
당신은 복잡한 작업을 여러 전문 에이전트에게 라우팅하는 Orchestrator입니다.

사용 가능한 에이전트:
{agents_desc}

에이전트별 전문 분야:
- langgraph: 산술 계산 (덧셈, 뺄셈, 곱셈, 나눗셈 등), 날짜/시간 정보 제공
- mcp: 웹 검색 및 최신 정보 조회 (Tavily API 사용)
  * AI/기술 트렌드, 최신 뉴스, 프로그래밍 정보 등
  * 실시간 인터넷 정보가 필요한 모든 질문

작업 방식:
1. 사용자 질문을 분석하여 필요한 작업들을 식별
2. 각 작업에 적합한 에이전트를 선택
   - 계산 → langgraph
   - 웹 검색/최신 정보 → mcp
3. send_message 함수를 호출하여 작업 위임
4. 에이전트의 응답을 받은 후 다음 작업 진행 또는 최종 답변 생성

중요 규칙:
- 각 작업마다 send_message를 1번씩만 호출
- 에이전트 응답에 "에러" 또는 "시간 초과"가 포함되면 재시도하지 말고 바로 최종 답변 생성
- 에러가 발생한 작업은 "해당 정보를 가져올 수 없습니다"로 처리하고 나머지 결과로 답변
- 모든 필요한 작업이 완료되거나 에러가 발생하면 즉시 최종 답변 생성
- 불필요한 반복 호출 금지

예시:
질문: "2+2 계산하고, 2025년 AI 트렌드도 검색해줘"
→ 1. send_message("langgraph", "2+2를 계산해줘")
→ 2. send_message("mcp", "2025년 AI 트렌드를 검색해줘")
→ 3. 두 결과를 통합하여 최종 답변 (에러 발생 시에도 바로 답변)
"""

        # 대화 이력에 사용자 질문 추가
        messages = [ # [ 3 ]
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_query},
        ]

        # send_message 함수 선언
        send_message_tool = { # [ 4 ]
            "type": "function",
            "function": {
                "name": "send_message",
                "description": "특정 에이전트에게 작업을 전달합니다. 여러 번 호출 가능합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": f"호출할 에이전트 이름. 선택 가능: {', '.join(self.agents.keys())}",
                            "enum": list(self.agents.keys()),
                        },
                        "task": {
                            "type": "string",
                            "description": "에이전트에게 전달할 작업 내용",
                        },
                    },
                    "required": ["agent_name", "task"],
                },
            },
        }

        try:
            # 최대 6번의 함수 호출 허용 (무한 루프 방지)
            max_iterations = 6 # [ 1 ]
            iteration = 0
            function_calls_made = 0  # 실제로 함수를 호출한 횟수

            while iteration < max_iterations:
                iteration += 1
                print(f"\n🔄 반복 {iteration}:")

                response = await self.openai_client.chat.completions.create( # [ 2 ]
                    model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                    messages=messages,
                    tools=[send_message_tool],
                    tool_choice="auto",
                    temperature=0.1,
                )

                message = response.choices[0].message

                # Case 1: 함수 호출이 있는 경우
                if message.tool_calls: # [ 3 ]
                    messages.append(message)

                    # 모든 함수 호출 처리
                    for tool_call in message.tool_calls:
                        if tool_call.function.name == 'send_message':
                            function_calls_made += 1

                            # 함수 인자 추출
                            args = json.loads(tool_call.function.arguments)
                            agent_name = args.get('agent_name', '')
                            task = args.get('task', '')

                            print(f"  🎯 {agent_name} 에이전트 호출 중... (#{function_calls_made})")

                            # 실제 에이전트 호출
                            result = await self._call_agent(agent_name, task)

                            # 함수 호출 결과를 대화에 추가
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result,
                            })

                            print(f"  ✅ 결과: {result[:100]}...")

                    # 함수 호출 후 다음 반복으로 (GPT가 추가 작업 또는 최종 답변 생성)
                    continue

                # Case 2: 함수 호출 없이 직접 답변한 경우 (일반 응답 또는 최종 통합 답변)
                elif message.content: # [ 4 ]
                    return message.content

                # Case 3: 함수 호출도 없고 내용도 없는 비정상 상황 (거의 발생하지 않음)
                else: # [ 5 ]
                    return "응답을 생성할 수 없습니다"

            return "작업이 너무 복잡하여 완료할 수 없습니다. 질문을 단순화해주세요."

        except Exception as e:
            return f"Orchestrator 오류: {str(e)}"

    async def close(self):
        """리소스 정리"""
        if self.httpx_client:
            await self.httpx_client.aclose()


async def main():
    agent_urls = { # [ 1 ]
        'langgraph': 'http://localhost:10001',
        'mcp': 'http://localhost:10002',
    }

    orchestrator = AgentOrchestrator(agent_urls)

    try:
        await orchestrator.initialize() # [ 2 ]

        test_queries = [ # [ 3 ]
            "안녕하세요!",
            "현재 시각은?",
            "2025년 AI 에이전트 트렌드는?",
            "1752 + 2523를 계산하고, 2025년 AI 트렌드도 검색해주세요",
            "현재 시각과 함께, 파이썬 최신 버전도 알려주세요",
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n[테스트 {i}/{len(test_queries)}]")

            response = await orchestrator.process_query(query)

            print(f"\n최종 통합 응답: {response}")

            if i < len(test_queries):
                await asyncio.sleep(3)

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await orchestrator.close()


if __name__ == '__main__':
    asyncio.run(main())

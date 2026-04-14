"""
에이전트 설정 및 URL 관리
"""
from typing import Dict
from pydantic import BaseModel
import os


class AgentConfig(BaseModel):
    """에이전트 설정"""
    name: str
    url: str
    port: int
    description: str


# 에이전트 URL 설정
AGENT_CONFIGS: Dict[str, AgentConfig] = {
    "orchestrator": AgentConfig(
        name="Orchestrator Agent",
        url="http://localhost:10010",
        port=10010,
        description="사용자 요청을 분석하고 작업을 조율하는 중앙 오케스트레이터"
    ),
    "web_research": AgentConfig(
        name="Web Research Agent",
        url="http://localhost:10011",
        port=10011,
        description="MCP 기반 외부 웹 검색 및 정보 수집 에이전트"
    ),
    "internal_rag": AgentConfig(
        name="Internal RAG Agent",
        url="http://localhost:10012",
        port=10012,
        description="사내 문서/DB 기반 RAG 검색 및 답변 생성 에이전트"
    ),
    "file_management": AgentConfig(
        name="File Management Agent",
        url="http://localhost:10013",
        port=10013,
        description="Google Drive 기반 파일 관리 에이전트"
    ),
}


def get_agent_urls() -> Dict[str, str]:
    """에이전트 URL 딕셔너리 반환"""
    return {name: config.url for name, config in AGENT_CONFIGS.items()}


def get_agent_config(agent_name: str) -> AgentConfig:
    """특정 에이전트 설정 반환"""
    if agent_name not in AGENT_CONFIGS:
        raise ValueError(f"Unknown agent: {agent_name}")
    return AGENT_CONFIGS[agent_name]

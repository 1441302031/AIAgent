from __future__ import annotations

from typing import Iterator

from aiagent.agents.assistant import AssistantAgent
from aiagent.domain.models import AgentRequest, AgentResponse, CompletionEvent
from aiagent.providers.base import CompletionProvider
from aiagent.session.history import SessionHistory

PLANNER_SYSTEM_PROMPT = (
    "You are a planning specialist. Break the user's task into clear, actionable steps. "
    "Prefer concise numbered steps and practical structure."
)


class PlannerSubAgent:
    role_name = "planner"

    def __init__(
        self,
        provider: CompletionProvider,
        history: SessionHistory,
        model: str,
        temperature: float = 0.0,
    ) -> None:
        self._assistant = AssistantAgent(
            provider=provider,
            history=history,
            model=model,
            temperature=temperature,
            system_prompt=PLANNER_SYSTEM_PROMPT,
        )

    def run(self, request: AgentRequest) -> AgentResponse:
        return self._assistant.run(request)

    def run_stream(self, request: AgentRequest) -> Iterator[CompletionEvent]:
        return self._assistant.run_stream(request)

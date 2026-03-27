from __future__ import annotations

from typing import Iterator

from aiagent.domain.models import AgentRequest, AgentResponse, CompletionEvent


class CoordinatorAgent:
    def __init__(self, primary_agent, planner_agent, router, show_subagents: bool = False) -> None:
        self._primary_agent = primary_agent
        self._planner_agent = planner_agent
        self._router = router
        self._show_subagents = show_subagents

    def run(self, request: AgentRequest) -> AgentResponse:
        route = self._router.select(request)
        if route == "planner":
            response = self._planner_agent.run(request)
            handoff = {
                "agent": "planner",
                "reason": "task_router",
                "input_summary": request.user_input[:80],
                "result_summary": response.final_text[:80],
            }
            return AgentResponse(
                final_text=response.final_text,
                messages=response.messages,
                artifacts=response.artifacts,
                handoffs=[*response.handoffs, handoff],
            )

        return self._primary_agent.run(request)

    def run_stream(self, request: AgentRequest) -> Iterator[CompletionEvent]:
        route = self._router.select(request)
        if self._show_subagents:
            if route == "planner":
                yield CompletionEvent(kind="content", text="[planner]\n")
                yield from self._planner_agent.run_stream(request)
                return

            yield CompletionEvent(kind="content", text="[primary]\n")
            yield from self._primary_agent.run_stream(request)
            return

        response = self.run(request)
        yield CompletionEvent(kind="content", text=response.final_text)
        yield CompletionEvent(kind="done")

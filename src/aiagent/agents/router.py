from __future__ import annotations

from aiagent.domain.models import AgentRequest


class TaskRouter:
    _planner_keywords = (
        "plan",
        "planning",
        "steps",
        "break down",
        "拆解",
        "步骤",
        "计划",
        "方案",
    )

    def select(self, request: AgentRequest) -> str:
        override = request.metadata.get("route")
        if isinstance(override, str) and override.strip():
            return override.strip().lower()

        normalized = request.user_input.lower()
        if any(keyword in normalized for keyword in self._planner_keywords):
            return "planner"
        return "direct"

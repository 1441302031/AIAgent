from typing import Protocol

from aiagent.domain.models import AgentRequest, AgentResponse


class Agent(Protocol):
    def run(self, request: AgentRequest) -> AgentResponse: ...

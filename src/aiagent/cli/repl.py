from __future__ import annotations

from aiagent.agents.assistant import AssistantAgent
from aiagent.config.settings import Settings
from aiagent.domain.models import AgentRequest
from aiagent.providers.factory import create_provider
from aiagent.session.history import SessionHistory


def run_repl() -> int:
    settings = Settings.from_env()
    provider = create_provider(settings)
    agent = AssistantAgent(
        provider=provider,
        history=SessionHistory(),
        model=settings.model,
        temperature=settings.temperature,
    )

    while True:
        try:
            prompt = input("aiagent> ")
        except EOFError:
            return 0

        if prompt.lower() in {"quit", "exit"}:
            return 0
        if not prompt.strip():
            continue

        response = agent.run(AgentRequest(user_input=prompt))
        print(response.final_text)

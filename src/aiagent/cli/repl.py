from __future__ import annotations

import sys

from aiagent.agents.assistant import AssistantAgent
from aiagent.agents.coordinator import CoordinatorAgent
from aiagent.agents.router import TaskRouter
from aiagent.agents.subagent import PlannerSubAgent
from aiagent.cli.streaming import render_streaming_completion
from aiagent.config.settings import Settings
from aiagent.domain.models import AgentRequest
from aiagent.providers.factory import create_provider
from aiagent.session.history import SessionHistory


def run_repl(*, multi_agent: bool = False, show_subagents: bool = False) -> int:
    settings = Settings.from_env()
    provider = create_provider(settings)
    if multi_agent:
        shared_history = SessionHistory()
        agent = CoordinatorAgent(
            primary_agent=AssistantAgent(
                provider=provider,
                history=shared_history,
                model=settings.model,
                temperature=settings.temperature,
            ),
            planner_agent=PlannerSubAgent(
                provider=provider,
                history=shared_history,
                model=settings.model,
                temperature=settings.temperature,
            ),
            router=TaskRouter(),
            show_subagents=show_subagents,
        )
    else:
        agent = AssistantAgent(
            provider=provider,
            history=SessionHistory(),
            model=settings.model,
            temperature=settings.temperature,
        )

    while True:
        try:
            prompt = input("aiagent> ")
            normalized_prompt = prompt.strip()

            if normalized_prompt.lower() in {"quit", "exit"}:
                return 0
            if not normalized_prompt:
                continue

            render_streaming_completion(
                agent.run_stream(AgentRequest(user_input=prompt)),
                writer=sys.stdout,
            )
        except EOFError:
            return 0
        except KeyboardInterrupt:
            print()
            return 0

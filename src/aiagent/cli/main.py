from __future__ import annotations

import argparse
import sys

from aiagent.agents.assistant import AssistantAgent
from aiagent.agents.coordinator import CoordinatorAgent
from aiagent.agents.router import TaskRouter
from aiagent.agents.subagent import PlannerSubAgent
from aiagent.cli.repl import run_repl
from aiagent.cli.streaming import render_streaming_completion
from aiagent.config.settings import Settings
from aiagent.domain.models import AgentRequest
from aiagent.providers.factory import create_provider
from aiagent.session.history import SessionHistory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aiagent")
    parser.add_argument("prompt", nargs="?")
    parser.add_argument("--repl", action="store_true")
    parser.add_argument("--multi-agent", action="store_true")
    parser.add_argument("--show-subagents", action="store_true")
    args = parser.parse_args(argv)

    if args.repl:
        if args.multi_agent:
            if args.show_subagents:
                return run_repl(multi_agent=True, show_subagents=True)
            return run_repl(multi_agent=True)
        return run_repl()

    if not args.prompt:
        parser.error("a prompt is required unless --repl is set")

    settings = Settings.from_env()
    provider = create_provider(settings)
    if args.multi_agent:
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
            show_subagents=args.show_subagents,
        )
    else:
        agent = AssistantAgent(
            provider=provider,
            history=SessionHistory(),
            model=settings.model,
            temperature=settings.temperature,
        )
    render_streaming_completion(
        agent.run_stream(AgentRequest(user_input=args.prompt)),
        writer=sys.stdout,
    )
    return 0

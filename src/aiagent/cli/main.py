from __future__ import annotations

import argparse

from aiagent.agents.assistant import AssistantAgent
from aiagent.config.settings import Settings
from aiagent.domain.models import AgentRequest
from aiagent.providers.factory import create_provider
from aiagent.session.history import SessionHistory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aiagent")
    parser.add_argument("prompt", nargs="?")
    parser.add_argument("--repl", action="store_true")
    args = parser.parse_args(argv)

    if args.repl:
        from aiagent.cli.repl import run_repl

        return run_repl()

    if not args.prompt:
        parser.error("a prompt is required unless --repl is set")

    settings = Settings.from_env()
    provider = create_provider(settings)
    agent = AssistantAgent(
        provider=provider,
        history=SessionHistory(),
        model=settings.model,
        temperature=settings.temperature,
    )
    response = agent.run(AgentRequest(user_input=args.prompt))
    print(response.final_text)
    return 0

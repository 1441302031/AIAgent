from aiagent.domain.models import Message


def build_messages(system_prompt: str, history: list[Message], user_input: str) -> list[Message]:
    return [
        Message(role="system", content=system_prompt),
        *history,
        Message(role="user", content=user_input),
    ]

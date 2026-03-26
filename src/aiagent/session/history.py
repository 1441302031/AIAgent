from aiagent.domain.models import Message


class SessionHistory:
    def __init__(self) -> None:
        self._messages: list[Message] = []

    def add(self, message: Message) -> None:
        self._messages.append(message)

    def all(self) -> list[Message]:
        return list(self._messages)

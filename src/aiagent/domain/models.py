from dataclasses import dataclass, field


@dataclass(slots=True)
class Message:
    role: str
    content: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class CompletionRequest:
    model: str
    messages: list[Message]


@dataclass(slots=True)
class CompletionResponse:
    model: str
    message: Message


@dataclass(slots=True)
class AgentRequest:
    user_input: str


@dataclass(slots=True)
class AgentResponse:
    final_text: str

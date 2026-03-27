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
    temperature: float = 0.0


@dataclass(slots=True)
class CompletionResponse:
    model: str
    message: Message
    raw: dict = field(default_factory=dict)


@dataclass(slots=True)
class CompletionEvent:
    kind: str
    text: str = ""


@dataclass(slots=True)
class AgentRequest:
    user_input: str
    task_id: str | None = None
    context: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class AgentResponse:
    final_text: str
    messages: list[Message] = field(default_factory=list)
    artifacts: list[dict] = field(default_factory=list)
    handoffs: list[dict] = field(default_factory=list)

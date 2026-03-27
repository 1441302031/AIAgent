import aiagent.agents as agents

from aiagent.agents.assistant import AssistantAgent
from aiagent.agents.base import Agent
from aiagent.domain.models import AgentRequest, CompletionEvent, CompletionRequest, CompletionResponse, Message
from aiagent.prompts.system import DEFAULT_SYSTEM_PROMPT
from aiagent.providers.mock import MockProvider
from aiagent.session.history import SessionHistory


class CapturingProvider:
    def __init__(self, response_text: str = "captured") -> None:
        self.request: CompletionRequest | None = None
        self._response_text = response_text

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        self.request = request
        return CompletionResponse(
            model=request.model,
            message=Message(role="assistant", content=self._response_text),
        )


class StreamingProvider:
    def __init__(self, events: list[tuple[str, str]] | None = None) -> None:
        self.request: CompletionRequest | None = None
        self.events = events or [("content", "hello"), ("content", " world"), ("done", "")]

    def stream_complete(self, request: CompletionRequest):
        self.request = request
        for kind, text in self.events:
            yield CompletionEvent(kind=kind, text=text)


class FailingStreamingProvider:
    def __init__(self) -> None:
        self.request: CompletionRequest | None = None

    def stream_complete(self, request: CompletionRequest):
        self.request = request
        yield CompletionEvent(kind="content", text="hello")
        raise ValueError("boom")


def test_assistant_agent_adds_user_and_assistant_messages_to_history():
    history = SessionHistory()
    agent = AssistantAgent(
        provider=MockProvider(mode="scripted", scripted_response="done"),
        history=history,
        model="mock-model",
    )

    response = agent.run(AgentRequest(user_input="help me"))

    assert response.final_text == "done"
    assert [m.role for m in history.all()] == ["user", "assistant"]


def test_assistant_agent_includes_prior_history_in_provider_request():
    history = SessionHistory()
    history.add(Message(role="assistant", content="prior"))
    provider = CapturingProvider(response_text="done")
    agent = AssistantAgent(provider=provider, history=history, model="mock-model")

    response = agent.run(AgentRequest(user_input="hello"))

    assert response.final_text == "done"
    assert provider.request is not None
    assert [(message.role, message.content) for message in provider.request.messages] == [
        ("system", DEFAULT_SYSTEM_PROMPT),
        ("assistant", "prior"),
        ("user", "hello"),
    ]


def test_assistant_agent_streams_content_and_updates_history():
    history = SessionHistory()
    provider = StreamingProvider()
    agent = AssistantAgent(provider=provider, history=history, model="mock-model")

    events = list(agent.run_stream(AgentRequest(user_input="help me")))

    assert provider.request is not None
    assert [(event.kind, event.text) for event in events] == [
        ("content", "hello"),
        ("content", " world"),
        ("done", ""),
    ]
    assert [m.role for m in history.all()] == ["user", "assistant"]
    assert history.all()[-1].content == "hello world"


def test_assistant_agent_streams_writes_partial_history_when_closed_before_done():
    history = SessionHistory()
    provider = StreamingProvider()
    agent = AssistantAgent(provider=provider, history=history, model="mock-model")

    stream = agent.run_stream(AgentRequest(user_input="help me"))
    first_event = next(stream)
    assert (first_event.kind, first_event.text) == ("content", "hello")

    stream.close()

    assert provider.request is not None
    assert [m.role for m in history.all()] == ["user", "assistant"]
    assert history.all()[-1].content == "hello"


def test_assistant_agent_streams_preserves_user_history_when_provider_raises():
    history = SessionHistory()
    provider = FailingStreamingProvider()
    agent = AssistantAgent(provider=provider, history=history, model="mock-model")

    stream = agent.run_stream(AgentRequest(user_input="help me"))
    assert next(stream).text == "hello"

    try:
        next(stream)
    except ValueError as exc:
        assert str(exc) == "boom"
    else:
        raise AssertionError("Expected provider failure")

    assert provider.request is not None
    assert [m.role for m in history.all()] == ["user"]
    assert history.all()[0].content == "help me"


def test_aiagent_agents_re_exports_public_agent_types():
    assert agents.Agent is Agent
    assert agents.AssistantAgent is AssistantAgent

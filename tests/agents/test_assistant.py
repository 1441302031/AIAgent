import aiagent.agents as agents

from aiagent.agents.assistant import AssistantAgent
from aiagent.agents.base import Agent
from aiagent.domain.models import AgentRequest, CompletionRequest, CompletionResponse, Message
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


def test_aiagent_agents_re_exports_public_agent_types():
    assert agents.Agent is Agent
    assert agents.AssistantAgent is AssistantAgent

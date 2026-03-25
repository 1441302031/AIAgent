from aiagent.agents.assistant import AssistantAgent
from aiagent.domain.models import AgentRequest, Message
from aiagent.providers.mock import MockProvider
from aiagent.session.history import SessionHistory


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
    agent = AssistantAgent(provider=MockProvider(mode="echo"), history=history, model="mock-model")

    response = agent.run(AgentRequest(user_input="hello"))

    assert response.final_text == "Mock echo: hello"

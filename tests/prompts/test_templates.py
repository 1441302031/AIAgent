from aiagent.domain.models import Message
from aiagent.prompts.templates import build_messages
from aiagent.session.history import SessionHistory


def test_build_messages_prepends_system_prompt():
    history = SessionHistory()
    history.add(Message(role="assistant", content="earlier"))
    messages = build_messages("system text", history.all(), "next user input")
    assert messages[0].role == "system"
    assert messages[-1].content == "next user input"

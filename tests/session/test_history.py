from aiagent.domain.models import Message
from aiagent.session.history import SessionHistory


def test_session_history_appends_messages_in_order():
    history = SessionHistory()
    history.add(Message(role="user", content="hello"))
    history.add(Message(role="assistant", content="hi"))
    assert [m.role for m in history.all()] == ["user", "assistant"]

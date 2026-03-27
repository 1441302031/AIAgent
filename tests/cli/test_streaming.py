from __future__ import annotations

from io import StringIO

from aiagent.cli.streaming import render_streaming_completion
from aiagent.domain.models import CompletionEvent


class RecordingWriter:
    def __init__(self) -> None:
        self.chunks: list[str] = []
        self._buffer = StringIO()

    def write(self, text: str) -> int:
        self.chunks.append(text)
        return self._buffer.write(text)

    def flush(self) -> None:
        pass

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._buffer.seek(offset, whence)

    def truncate(self, size: int | None = None) -> int:
        return self._buffer.truncate(size)

    def getvalue(self) -> str:
        return self._buffer.getvalue()


class FaultyClearWriter(RecordingWriter):
    def seek(self, offset: int, whence: int = 0) -> int:
        raise OSError("seek failed")

    def truncate(self, size: int | None = None) -> int:
        raise OSError("truncate failed")


class EncodingLimitedWriter(RecordingWriter):
    encoding = "gbk"

    def write(self, text: str) -> int:
        text.encode(self.encoding)
        return super().write(text)


class ClosableEventIterator:
    def __init__(self, events: list[CompletionEvent]) -> None:
        self._events = iter(events)
        self.closed = False

    def __iter__(self):
        return self

    def __next__(self) -> CompletionEvent:
        return next(self._events)

    def close(self) -> None:
        self.closed = True


def test_render_streaming_completion_shows_thinking_before_first_token():
    writer = RecordingWriter()

    result = render_streaming_completion(
        [CompletionEvent(kind="content", text="hello"), CompletionEvent(kind="done")],
        writer=writer,
        time_fn=lambda: 1.0,
    )

    assert result == "hello"
    assert writer.chunks[0].startswith("thinking")


def test_render_streaming_completion_falls_back_when_clear_methods_raise():
    writer = FaultyClearWriter()

    result = render_streaming_completion(
        [CompletionEvent(kind="content", text="hello"), CompletionEvent(kind="done")],
        writer=writer,
        time_fn=lambda: 1.0,
    )

    assert result == "hello"
    assert "\r" in writer.getvalue()
    assert "thinking" not in writer.getvalue().splitlines()[-1]


def test_render_streaming_completion_removes_thinking_from_final_output():
    writer = RecordingWriter()

    result = render_streaming_completion(
        [
            CompletionEvent(kind="content", text="hello"),
            CompletionEvent(kind="content", text=" world"),
            CompletionEvent(kind="done"),
        ],
        writer=writer,
        time_fn=lambda: 2.5,
    )

    assert result == "hello world"
    assert "thinking" not in writer.getvalue().splitlines()[-1]


def test_render_streaming_completion_ends_with_newline():
    writer = RecordingWriter()

    result = render_streaming_completion(
        [CompletionEvent(kind="content", text="hello"), CompletionEvent(kind="done")],
        writer=writer,
        time_fn=lambda: 0.0,
    )

    assert result == "hello"
    assert writer.getvalue().endswith("\n")


def test_render_streaming_completion_replaces_characters_unencodable_for_writer():
    writer = EncodingLimitedWriter()

    result = render_streaming_completion(
        [CompletionEvent(kind="content", text="hello 😊"), CompletionEvent(kind="done")],
        writer=writer,
        time_fn=lambda: 0.0,
    )

    assert result == "hello 😊"
    assert writer.getvalue().endswith("\n")
    assert "hello ?" in writer.getvalue()


def test_render_streaming_completion_closes_event_iterator_after_done():
    writer = RecordingWriter()
    events = ClosableEventIterator(
        [CompletionEvent(kind="content", text="hello"), CompletionEvent(kind="done")]
    )

    result = render_streaming_completion(
        events,
        writer=writer,
        time_fn=lambda: 0.0,
    )

    assert result == "hello"
    assert events.closed is True

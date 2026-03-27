from __future__ import annotations

from collections.abc import Iterable
from sys import stdout
from time import monotonic
from typing import TextIO

from aiagent.domain.models import CompletionEvent


def _safe_write(writer: TextIO, text: str) -> None:
    try:
        writer.write(text)
        return
    except UnicodeEncodeError:
        encoding = getattr(writer, "encoding", None)
        if not encoding:
            raise

    sanitized = text.encode(encoding, errors="replace").decode(encoding)
    writer.write(sanitized)


def _clear_writer(writer: TextIO, line_length: int) -> None:
    if hasattr(writer, "seek") and hasattr(writer, "truncate"):
        try:
            writer.seek(0)
            writer.truncate(0)
            return
        except Exception:
            pass

    _safe_write(writer, "\r" + (" " * line_length) + "\r")


def render_streaming_completion(
    events: Iterable[CompletionEvent],
    *,
    writer: TextIO = stdout,
    time_fn=monotonic,
) -> str:
    start = time_fn()
    thinking_line = f"thinking... {time_fn() - start:.1f}s"
    _safe_write(writer, thinking_line)
    writer.flush()

    final_text = ""
    saw_content = False

    try:
        for event in events:
            if event.kind != "content":
                if event.kind == "done":
                    break
                continue

            if not saw_content:
                _clear_writer(writer, len(thinking_line))
                saw_content = True

            _safe_write(writer, event.text)
            writer.flush()
            final_text += event.text
    finally:
        close = getattr(events, "close", None)
        if callable(close):
            close()

    if not saw_content:
        _clear_writer(writer, len(thinking_line))

    _safe_write(writer, "\n")
    writer.flush()
    return final_text

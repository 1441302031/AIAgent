from importlib import import_module
import os
from pathlib import Path
import shutil
import uuid

import pytest


_LOCAL_TMP_ROOT = Path(__file__).resolve().parent / ".pytest-tmp"


@pytest.fixture
def tmp_path(request):
    _LOCAL_TMP_ROOT.mkdir(exist_ok=True)
    path = _LOCAL_TMP_ROOT / f"{request.node.name}-{os.getpid()}-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def load_target():
    return import_module("tools.run_with_env")


def test_parse_env_file_ignores_comments_and_blank_lines(tmp_path: Path):
    target = load_target()
    env_file = tmp_path / ".env.test"
    env_file.write_text(
        "# comment\n\nAIAGENT_PROVIDER=deepseek\nAIAGENT_MODEL=deepseek-chat\n",
        encoding="utf-8",
    )

    result = target.parse_env_file(env_file)

    assert result == {
        "AIAGENT_PROVIDER": "deepseek",
        "AIAGENT_MODEL": "deepseek-chat",
    }


def test_resolve_env_file_supports_builtin_provider_names(tmp_path: Path):
    project_root = tmp_path

    assert load_target().resolve_env_file(project_root, provider_name="mock", explicit_env=None) == project_root / ".env.mock"
    assert load_target().resolve_env_file(project_root, provider_name="deepseek", explicit_env=None) == project_root / ".env.deepseek"
    assert load_target().resolve_env_file(project_root, provider_name="moonshot", explicit_env=None) == project_root / ".env.moonshot"


def test_resolve_env_file_rejects_unknown_provider(tmp_path: Path):
    with pytest.raises(ValueError, match="Unsupported provider"):
        load_target().resolve_env_file(tmp_path, provider_name="unknown", explicit_env=None)


def test_resolve_env_file_uses_explicit_env_path_as_provided(tmp_path: Path, monkeypatch):
    target = load_target()
    project_root = tmp_path / "repo"
    absolute_env = tmp_path / "configs" / ".env.custom"

    monkeypatch.chdir(tmp_path)

    assert target.resolve_env_file(project_root, provider_name=None, explicit_env=str(absolute_env)) == absolute_env
    assert target.resolve_env_file(project_root, provider_name=None, explicit_env="configs/.env.custom") == project_root / "configs" / ".env.custom"


def test_ensure_env_file_exists_rejects_missing_file(tmp_path: Path):
    missing = tmp_path / ".env.missing"

    with pytest.raises(FileNotFoundError, match=str(missing.name)):
        load_target().ensure_env_file_exists(missing)


def test_build_runtime_mode_rejects_missing_mode():
    with pytest.raises(ValueError, match="prompt or repl"):
        load_target().build_runtime_mode(prompt=None, repl=False)


def test_build_runtime_mode_rejects_conflicting_modes():
    with pytest.raises(ValueError, match="choose exactly one"):
        load_target().build_runtime_mode(prompt="hi", repl=True)


def test_parse_env_file_rejects_invalid_line(tmp_path: Path):
    target = load_target()
    env_file = tmp_path / ".env.bad"
    env_file.write_text("AIAGENT_PROVIDER=deepseek\nINVALID_LINE\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid .env line"):
        target.parse_env_file(env_file)


def test_build_aiagent_command_builds_one_shot_command():
    command = load_target().build_aiagent_command("python", prompt="hello", repl=False)

    assert command == ["python", "-m", "aiagent", "hello"]


def test_build_aiagent_command_builds_repl_command():
    command = load_target().build_aiagent_command("python", prompt=None, repl=True)

    assert command == ["python", "-m", "aiagent", "--repl"]


def test_build_verbose_summary_redacts_sensitive_values():
    summary = load_target().build_verbose_summary(
        env_file=".env.deepseek",
        mode="prompt",
        provider_name="deepseek",
        env_values={
            "AIAGENT_PROVIDER": "deepseek",
            "AIAGENT_DEEPSEEK_API_KEY": "secret",
        },
    )

    assert ".env.deepseek" in summary
    assert "deepseek" in summary
    assert "secret" not in summary


def test_main_prepends_src_to_pythonpath_and_merges_existing_pythonpath(tmp_path: Path, monkeypatch):
    target = load_target()
    captured = {}

    def fake_run(command, env, cwd):
        captured["command"] = command
        captured["env"] = env
        captured["cwd"] = cwd

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setenv("PYTHONPATH", "existing/path")
    monkeypatch.setattr(target.subprocess, "run", fake_run)

    exit_code = target.main(["mock", "--prompt", "hello"])

    assert exit_code == 0
    assert captured["cwd"] == Path(target.__file__).resolve().parent.parent
    assert captured["command"] == [target.sys.executable, "-m", "aiagent", "hello"]
    assert captured["env"]["PYTHONPATH"] == str(captured["cwd"] / "src") + os.pathsep + "existing/path"

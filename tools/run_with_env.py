from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


BUILTIN_ENV_FILES: dict[str, str] = {
    "mock": ".env.mock",
    "deepseek": ".env.deepseek",
    "moonshot": ".env.moonshot",
}

SENSITIVE_KEY_MARKERS = ("KEY", "SECRET", "TOKEN", "PASSWORD")


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid .env line: {raw_line}")
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def resolve_env_file(project_root: Path, provider_name: str | None, explicit_env: str | None) -> Path:
    if explicit_env:
        explicit_path = Path(explicit_env)
        return explicit_path if explicit_path.is_absolute() else project_root / explicit_path
    if provider_name not in BUILTIN_ENV_FILES:
        raise ValueError(f"Unsupported provider: {provider_name}")
    return project_root / BUILTIN_ENV_FILES[provider_name]


def ensure_env_file_exists(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"Environment file not found: {path}")
    return path


def build_runtime_mode(prompt: str | None, repl: bool) -> str:
    if bool(prompt) == bool(repl):
        if prompt or repl:
            raise ValueError("Must choose exactly one of --prompt or --repl.")
        raise ValueError("You must provide prompt or repl.")
    return "repl" if repl else "prompt"


def build_aiagent_command(python_executable: str, prompt: str | None, repl: bool) -> list[str]:
    if repl:
        return [python_executable, "-m", "aiagent", "--repl"]
    if prompt is None:
        raise ValueError("Prompt is required unless repl is enabled.")
    return [python_executable, "-m", "aiagent", prompt]


def build_verbose_summary(
    *,
    env_file: str,
    mode: str,
    provider_name: str | None,
    env_values: dict[str, str],
) -> str:
    safe_keys = sorted(
        key for key in env_values if not any(marker in key.upper() for marker in SENSITIVE_KEY_MARKERS)
    )
    keys = ", ".join(safe_keys) if safe_keys else "<none>"
    provider = provider_name or "<custom>"
    return f"env_file={env_file} mode={mode} provider={provider} keys={keys}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_with_env")
    parser.add_argument("provider", nargs="?")
    parser.add_argument("--env")
    parser.add_argument("--prompt")
    parser.add_argument("--repl", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def run_aiagent(command: list[str], child_env: dict[str, str], cwd: Path) -> int:
    return subprocess.run(command, env=child_env, cwd=cwd).returncode


def build_child_env(project_root: Path, env_values: dict[str, str]) -> dict[str, str]:
    child_env = os.environ.copy()
    child_env.update(env_values)
    pythonpath_parts = [str(project_root / "src")]
    existing_pythonpath = child_env.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    child_env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    return child_env


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list:
        for provider_name in BUILTIN_ENV_FILES:
            print(provider_name)
        return 0

    if not args.provider and not args.env:
        parser.error("provider or --env is required")

    try:
        mode = build_runtime_mode(args.prompt, args.repl)
        project_root = Path(__file__).resolve().parent.parent
        env_file = ensure_env_file_exists(
            resolve_env_file(project_root, args.provider, args.env)
        )
        env_values = parse_env_file(env_file)
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))

    command = build_aiagent_command(sys.executable, args.prompt, args.repl)
    child_env = build_child_env(project_root, env_values)

    if args.verbose:
        provider_name = args.provider or env_values.get("AIAGENT_PROVIDER")
        print(
            build_verbose_summary(
                env_file=str(env_file),
                mode=mode,
                provider_name=provider_name,
                env_values=env_values,
            )
        )

    return run_aiagent(command, child_env, project_root)


if __name__ == "__main__":
    raise SystemExit(main())

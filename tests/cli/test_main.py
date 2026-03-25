from importlib import import_module

from aiagent.cli.main import main


def test_package_entrypoint_module_exists():
    module = import_module("aiagent.__main__")
    assert module is not None


def test_main_prints_one_shot_response(capsys):
    exit_code = main(["hello"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Mock echo: hello" in captured.out

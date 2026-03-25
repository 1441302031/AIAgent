from importlib import import_module


def test_package_entrypoint_module_exists():
    module = import_module("aiagent.__main__")
    assert module is not None

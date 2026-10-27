import pytest

from ado_mcp.config import Settings


@pytest.fixture(autouse=True)
def ado_env(monkeypatch):
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setenv("ADO_ORG", "myorg")
    monkeypatch.setenv("ADO_PROJECT", "myproject")
    monkeypatch.setenv("ADO_PAT", "mypat")

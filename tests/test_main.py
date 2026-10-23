import pytest

from ado_mcp import server


@pytest.fixture
def run_calls(monkeypatch):
    calls = []
    monkeypatch.setattr(server.mcp, "run", lambda **kwargs: calls.append(kwargs))
    return calls


def test_main_defaults_to_stdio(monkeypatch, run_calls):
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    server.main()
    assert run_calls == [{}]


def test_main_http_binds_to_localhost(monkeypatch, run_calls):
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    server.main()
    assert run_calls == [
        {
            "transport": "http",
            "host": "127.0.0.1",
            "port": 8000,
            "host_origin_protection": True,
        }
    ]


def test_main_rejects_unknown_transport(monkeypatch, run_calls):
    monkeypatch.setenv("MCP_TRANSPORT", "htp")
    with pytest.raises(SystemExit, match="Unknown MCP_TRANSPORT='htp'"):
        server.main()
    assert run_calls == []

import pytest

from ado_mcp import server


class FakeServer:
    def __init__(self):
        self.run_calls = []

    def run(self, **kwargs):
        self.run_calls.append(kwargs)


@pytest.fixture
def fake_server(monkeypatch):
    fake = FakeServer()
    monkeypatch.setattr(server, "create_server", lambda: fake)
    return fake


def test_main_defaults_to_stdio(monkeypatch, fake_server):
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    server.main()
    assert fake_server.run_calls == [{}]


def test_main_http_binds_to_localhost(monkeypatch, fake_server):
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    server.main()
    assert fake_server.run_calls == [
        {
            "transport": "http",
            "host": "127.0.0.1",
            "port": 8000,
            "host_origin_protection": True,
        }
    ]


def test_main_rejects_unknown_transport(monkeypatch, fake_server):
    monkeypatch.setenv("MCP_TRANSPORT", "htp")
    with pytest.raises(SystemExit, match="Unknown MCP_TRANSPORT='htp'"):
        server.main()
    assert fake_server.run_calls == []

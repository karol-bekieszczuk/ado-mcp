import httpx2

from ado_mcp.config import ADO_API_VERSION, Settings

ADO_TIMEOUT = httpx2.Timeout(10.0, connect=5.0)


def build_http_client(
    settings: Settings, transport: httpx2.AsyncBaseTransport | None = None
) -> httpx2.AsyncClient:
    return httpx2.AsyncClient(
        base_url=f"https://dev.azure.com/{settings.org}/{settings.project}/_apis/",
        auth=httpx2.BasicAuth("", settings.pat.get_secret_value()),
        params={"api-version": ADO_API_VERSION},
        timeout=ADO_TIMEOUT,
        follow_redirects=False,
        transport=transport,
    )

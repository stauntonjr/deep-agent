"""Existing SciFact MCP tools; service failures never become invented answers."""

import json

import httpx
from langchain_mcp_adapters.client import MultiServerMCPClient


class LimitedStream(httpx.AsyncByteStream):
    def __init__(self, inner, maximum):
        self.inner, self.maximum = inner, maximum

    async def __aiter__(self):
        total = 0
        async for chunk in self.inner:
            total += len(chunk)
            if total > self.maximum:
                raise ValueError("MCP response exceeds byte limit")
            yield chunk

    async def aclose(self):
        await self.inner.aclose()


class MCPTransport(httpx.AsyncBaseTransport):
    """Bound bytes while preserving maintained MCP JSON/SSE framing."""

    def __init__(self, inner=None, maximum=131072):
        self.inner = inner or httpx.AsyncHTTPTransport(retries=0)
        self.maximum = maximum

    async def handle_async_request(self, request):
        request.headers["Accept-Encoding"] = "identity"
        response = await self.inner.handle_async_request(request)
        if 300 <= response.status_code < 400:
            await response.aclose()
            raise ValueError("MCP redirects are forbidden")
        if response.headers.get("Content-Encoding", "identity").lower() != "identity":
            await response.aclose()
            raise ValueError("compressed MCP responses are forbidden")
        response.stream = LimitedStream(response.stream, self.maximum)
        return response

    async def aclose(self):
        await self.inner.aclose()


def mcp_http_client(headers=None, timeout=None, auth=None):
    return httpx.AsyncClient(
        headers=headers,
        timeout=httpx.Timeout(20),
        auth=auth,
        transport=MCPTransport(),
        trust_env=False,
        follow_redirects=False,
    )


def validate_result(name: str, result: dict) -> dict:
    schema = "mcp-answer-result/v1" if name == "answer_scifact" else "mcp-search-result/v1"
    if result.get("schema_version") != schema:
        raise ValueError("unexpected SciFact result schema")
    if name == "answer_scifact":
        if (
            not isinstance(result.get("text"), str)
            or not isinstance(result.get("citations"), list)
            or not isinstance(result.get("evidence"), list)
        ):
            raise ValueError("invalid SciFact answer")
        ids = {hit.get("doc_id") for hit in result["evidence"] if isinstance(hit, dict)}
        if any(citation not in ids for citation in result["citations"]):
            raise ValueError("citation outside supplied evidence")
    elif not isinstance(result.get("hits"), list):
        raise ValueError("invalid SciFact search")
    return result


class SciFactClient:
    def __init__(self, endpoint: str):
        self.client = MultiServerMCPClient(
            {
                "scifact": {
                    "url": endpoint,
                    "transport": "streamable_http",
                    "timeout": 20,
                    "httpx_client_factory": mcp_http_client,
                }
            },
            handle_tool_errors=False,
        )

    async def call(self, name: str, query: str) -> dict:
        tools = await self.client.get_tools()
        tool = next((tool for tool in tools if tool.name == name), None)
        if tool is None:
            raise ValueError("required SciFact tool unavailable")
        raw = await tool.ainvoke({"query": query, "limit": 5})
        if isinstance(raw, dict) and "structured_content" in raw:
            raw = raw["structured_content"]
        elif isinstance(raw, list):
            text = next(
                (
                    part.get("text")
                    for part in raw
                    if isinstance(part, dict) and part.get("type") == "text"
                ),
                None,
            )
            raw = json.loads(text) if text else None
        elif isinstance(raw, str):
            raw = json.loads(raw)
        if not isinstance(raw, dict) or len(json.dumps(raw)) > 131072:
            raise ValueError("invalid or oversized SciFact result")
        return validate_result(name, raw)

    async def search(self, query: str) -> dict:
        return await self.call("search_scifact", query)

    async def answer(self, query: str) -> dict:
        return await self.call("answer_scifact", query)

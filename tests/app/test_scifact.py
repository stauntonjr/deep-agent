import pytest

from deep_agent.scifact import validate_result


def test_citations_require_actual_supplied_evidence():
    with pytest.raises(ValueError):
        validate_result(
            "answer_scifact",
            {
                "schema_version": "mcp-answer-result/v1",
                "text": "Claim",
                "citations": ["invented"],
                "evidence": [],
            },
        )
    result = validate_result(
        "answer_scifact",
        {
            "schema_version": "mcp-answer-result/v1",
            "text": "insufficient evidence",
            "citations": [],
            "evidence": [],
        },
    )
    assert result["text"] == "insufficient evidence"
    with pytest.raises(ValueError):
        validate_result("answer_scifact", {"text": "fake"})


@pytest.mark.parametrize("sse", [False, True])
async def test_mcp_response_is_bounded_before_json_or_sse_parse(sse):
    import httpx

    from deep_agent.scifact import MCPTransport

    class Stream(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield b"x" * 100
            yield b"y" * 100

    transport = MCPTransport(
        httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                headers={"Content-Type": "text/event-stream" if sse else "application/json"},
                stream=Stream(),
            )
        ),
        maximum=128,
    )
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ValueError, match="limit"):
            await client.get("http://scifact/mcp")


async def test_mcp_same_origin_redirect_is_rejected_before_following():
    import httpx

    from deep_agent.scifact import MCPTransport

    calls = []

    def respond(request):
        calls.append(request.url.path)
        return httpx.Response(307, headers={"Location": "http://scifact/admin"})

    async with httpx.AsyncClient(
        transport=MCPTransport(httpx.MockTransport(respond)), follow_redirects=True
    ) as client:
        with pytest.raises(ValueError, match="redirect"):
            await client.get("http://scifact/mcp")
    assert calls == ["/mcp"]

import httpx
import pytest
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import a2a_pb2 as p

from deep_agent.bridge import build_bridge


@pytest.mark.parametrize(
    "question,state",
    [
        ("Investigate GPU-A", p.TASK_STATE_COMPLETED),
        ("Investigate GPU-A and GPU-B", p.TASK_STATE_INPUT_REQUIRED),
    ],
)
async def test_authenticated_sdk_bridge_read_only(question, state):
    calls = []

    def upstream(request):
        calls.append(request)
        assert request.method == "GET"
        if request.url.path.endswith("investigate"):
            return httpx.Response(
                200,
                json={
                    "status": "unresolved",
                    "required_quantity": None,
                    "evidence": [{"evidence_id": "source1"}],
                },
            )
        return httpx.Response(
            200, json={"evidence": {"evidence_id": "source1"}, "cells": {"C2": "conflict"}}
        )

    app = build_bridge(
        "http://bridge",
        "http://procurement",
        "t" * 32,
        upstream_transport=httpx.MockTransport(upstream),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://bridge"
    ) as http:
        assert (await http.get("/.well-known/agent-card.json")).status_code == 401
        http.headers["Authorization"] = "Bearer " + "t" * 32
        card = await A2ACardResolver(http, "http://bridge").get_agent_card()
        client = ClientFactory(
            ClientConfig(
                streaming=False,
                polling=False,
                httpx_client=http,
                supported_protocol_bindings=["JSONRPC"],
            )
        ).create(card)
        import json

        request = p.SendMessageRequest(
            message=p.Message(
                message_id="m1",
                role=p.ROLE_USER,
                parts=[
                    p.Part(
                        text=json.dumps(
                            {
                                "question": question,
                                "project": "atlas",
                                "as_of": "2026-10-01T00:00:00Z",
                            }
                        )
                    )
                ],
            )
        )
        async for event in client.send_message(request):
            assert event.task.status.state == state
            task = await client.get_task(p.GetTaskRequest(id=event.task.id))
            assert task.status.state == state
            if state == p.TASK_STATE_COMPLETED:
                artifact = json.loads(task.artifacts[0].parts[0].text)
                assert artifact["investigation"]["required_quantity"] is None
                assert artifact["sources"][0]["cells"]["C2"] == "conflict"
                assert len(calls) == 2
            else:
                assert calls == []


async def test_upstream_redirect_never_followed_or_replaced_with_evidence():
    from deep_agent.bridge import ProcurementHTTP

    calls = []

    def upstream(request):
        calls.append(request.url.path)
        return httpx.Response(307, headers={"Location": "http://procurement/admin"})

    service = ProcurementHTTP("http://procurement", transport=httpx.MockTransport(upstream))
    with pytest.raises(ValueError):
        await service.investigate("atlas", "GPU-A", "2026-10-01T00:00:00Z")
    assert calls == ["/api/corpus/investigate"]


async def test_bridge_rejects_invalid_token_host_and_large_body():
    app = build_bridge("http://bridge", "http://procurement", "t" * 32)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://bridge"
    ) as client:
        assert (
            await client.post("/rpc", headers={"Authorization": "Bearer wrong"}, json={})
        ).status_code == 401
        client.headers["Authorization"] = "Bearer " + "t" * 32
        assert (
            await client.get("/.well-known/agent-card.json", headers={"Host": "evil.test"})
        ).status_code == 400
        assert (await client.post("/rpc", content=b"x" * 16385)).status_code == 413


async def test_upstream_oversized_response_is_rejected_before_evidence():
    from deep_agent.bridge import ProcurementHTTP

    service = ProcurementHTTP(
        "http://procurement",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b"x" * 131073)),
    )
    with pytest.raises(ValueError, match="limit"):
        await service.investigate("atlas", "GPU-A", "2026-10-01T00:00:00Z")

import json

import httpx

from deep_agent.bridge import build_bridge
from deep_agent.config import Settings
from deep_agent.specialist import SpecialistClient
from deep_agent.store import Store


async def test_exchange_records_actual_scoped_request_and_bridge_reads(tmp_path):
    token = "x" * 48
    secret = tmp_path / "token"
    secret.write_text(token)
    secret.chmod(0o600)
    calls = []

    async def upstream(request):
        calls.append(request.url.path)
        if request.url.path.endswith("investigate"):
            return httpx.Response(
                200,
                json={
                    "required_quantity": "8",
                    "ordered_quantity": "6",
                    "evidence": [{"evidence_id": "source1"}],
                },
            )
        return httpx.Response(200, json={"evidence_id": "source1"})

    bridge = build_bridge(
        "http://127.0.0.1:8101", "http://upstream", token, httpx.MockTransport(upstream)
    )
    store = Store(tmp_path / "db")
    sid = store.create("alice")["id"]
    settings = Settings(service_token_file=secret)
    client = SpecialistClient(settings, store, transport=httpx.ASGITransport(app=bridge))
    events = []

    async def record(event):
        events.append(event)

    result = await client.investigate(
        "alice",
        sid,
        "Investigate GPU-A",
        "atlas",
        "2026-10-01T00:00:00Z",
        on_event=record,
        correlation_id="084c034a-f499-40c9-8412-188960b817c9",
    )
    assert result["state"] == "completed"
    assert [e["phase"] for e in events] == ["request", "response"]
    assert events[0]["question"] == "Investigate GPU-A"
    assert events[1]["remote_id"] == result["remote_id"]
    assert events[1]["correlation_id"] == events[0]["correlation_id"]
    assert result["observations"]["source_count"] == 1
    assert calls == ["/api/corpus/investigate", "/api/corpus/source"]
    assert token not in json.dumps(events)
    assert token not in json.dumps(result)


def test_tracing_requires_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    assert not Settings.from_env().langsmith_tracing
    monkeypatch.setenv("DEEPAGENT_LANGSMITH_TRACING", "1")
    assert Settings.from_env().langsmith_tracing


def test_disabled_export_does_not_read_key_or_construct_client(tmp_path, monkeypatch):
    import deep_agent.observability as observability

    def unexpected(**kwargs):
        raise AssertionError("Disabled tracing must not create an exporter")

    monkeypatch.setattr(observability, "Client", unexpected)
    assert observability.client_for(Settings(langsmith_key_file=tmp_path / "missing")) is None


def test_enabled_export_requires_credential(monkeypatch):
    import pytest

    from deep_agent.observability import client_for

    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    with pytest.raises(ValueError, match="requires"):
        client_for(Settings(langsmith_tracing=True))


async def test_sdk_parent_crosses_a2a_without_export(tmp_path, monkeypatch):
    from langsmith import trace
    from langsmith.run_trees import RunTree

    from deep_agent.observability import client_for, context_for

    spans = []
    monkeypatch.setenv("LANGSMITH_API_KEY", "test-only-not-a-credential")
    monkeypatch.setattr(RunTree, "post", lambda self, **kwargs: spans.append(self))
    monkeypatch.setattr(RunTree, "patch", lambda self, **kwargs: None)
    settings = Settings(langsmith_tracing=True)
    token = "x" * 48
    secret = tmp_path / "token"
    secret.write_text(token)
    secret.chmod(0o600)
    settings.service_token_file = secret

    async def upstream(request):
        if request.url.path.endswith("investigate"):
            return httpx.Response(200, json={"evidence": [{"evidence_id": "source1"}]})
        return httpx.Response(200, json={"evidence_id": "source1"})

    bridge = build_bridge(
        "http://127.0.0.1:8101", "http://upstream", token, httpx.MockTransport(upstream), settings
    )
    store = Store(tmp_path / "db")
    sid = store.create("alice")["id"]
    client = SpecialistClient(settings, store, httpx.ASGITransport(app=bridge))
    with context_for(settings, client_for(settings)), trace("test root") as root:
        result = await client.investigate(
            "alice", sid, "Investigate GPU-A", "atlas", "2026-10-01T00:00:00Z"
        )
    assert result["state"] == "completed"
    by_name = {span.name: span for span in spans}
    exchange = by_name["A2A SendMessage"]
    task = by_name["Procurement A2A task"]
    assert exchange.parent_run_id == root.id
    assert task.parent_run_id == exchange.id
    assert task.trace_id == root.id
    assert by_name["Procurement investigation read"].parent_run_id == task.id
    assert by_name["Procurement source read"].parent_run_id == task.id
    assert "parent_trace" not in json.dumps(result)
    assert token not in json.dumps(result)

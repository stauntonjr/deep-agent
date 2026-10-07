import httpx
import pytest
from simulated_specialist import make_simulator

from deep_agent.config import Settings
from deep_agent.specialist import SpecialistClient
from deep_agent.store import Store


@pytest.mark.parametrize("state", ["completed", "input_required", "failed", "canceled", "working"])
async def test_sdk_exchange_preserves_state_artifacts_and_owner(tmp_path, state):
    store = Store(tmp_path / "db")
    sid = store.create("alice")["id"]
    server = make_simulator("http://specialist", state=state)
    settings = Settings(specialist_url="http://specialist", simulated=True)
    client = SpecialistClient(settings, store, transport=httpx.ASGITransport(app=server))
    result = await client.investigate(
        "alice", sid, "Investigate GPU-A", "atlas", "2026-10-01T00:00:00Z"
    )
    assert result["state"] == state
    assert result["artifacts"][0]["text"] == "SIMULATED: requirement unresolved; source BOM!C2."
    assert (await client.status("alice", result["id"]))["remote_id"] == result["remote_id"]
    assert any(
        event["kind"] == "task" and event["task"]["id"] == result["id"]
        for event in store.owned("alice", sid)["events"]
    )
    with pytest.raises(KeyError):
        await client.status("bob", result["id"])
    assert server.state.calls == ["SendMessage", "GetTask"]


async def test_card_cannot_redirect_client_or_expose_private_response(tmp_path):
    store = Store(tmp_path / "db")
    sid = store.create("alice")["id"]
    server = make_simulator("http://evil.test")
    client = SpecialistClient(
        Settings(specialist_url="http://specialist", simulated=True),
        store,
        transport=httpx.ASGITransport(app=server),
    )
    with pytest.raises(ValueError, match="interface"):
        await client.investigate("alice", sid, "Investigate", "atlas", "2026-10-01T00:00:00Z")
    assert server.state.calls == []


async def test_oversized_artifact_and_unaware_cutoff_are_rejected(tmp_path):
    store = Store(tmp_path / "db")
    sid = store.create("alice")["id"]
    server = make_simulator("http://specialist", text="x" * 70000)
    client = SpecialistClient(
        Settings(specialist_url="http://specialist", simulated=True),
        store,
        transport=httpx.ASGITransport(app=server),
    )
    with pytest.raises(ValueError):
        await client.investigate("alice", sid, "Investigate", "atlas", "2026-10-01")
    with pytest.raises(ValueError):
        await client.investigate("alice", sid, "Investigate", "atlas", "2026-10-01T00:00:00Z")


async def test_same_host_wrong_rpc_path_and_foreign_task_are_rejected(tmp_path):
    from a2a.types import a2a_pb2 as p

    store = Store(tmp_path / "db")
    sid = store.create("alice")["id"]
    server = make_simulator("http://specialist/admin")
    client = SpecialistClient(
        Settings(specialist_url="http://specialist", simulated=True),
        store,
        transport=httpx.ASGITransport(app=server),
    )
    with pytest.raises(ValueError, match="interface"):
        await client.investigate("alice", sid, "Investigate", "atlas", "2026-10-01T00:00:00Z")
    assert server.state.calls == []
    with pytest.raises(ValueError):
        client.payload(p.Task(id="remote", status=p.TaskStatus(state=p.TASK_STATE_UNSPECIFIED)))


async def test_refreshed_completion_survives_history_export(tmp_path):
    from a2a.types import a2a_pb2 as p

    store = Store(tmp_path / "db")
    sid = store.create("alice")["id"]
    server = make_simulator("http://specialist", state="working")
    client = SpecialistClient(
        Settings(specialist_url="http://specialist", simulated=True),
        store,
        transport=httpx.ASGITransport(app=server),
    )
    initial = await client.investigate("alice", sid, "Investigate", "atlas", "2026-10-01T00:00:00Z")
    store.event("alice", sid, {"kind": "task", "task": initial})
    from a2a.server.context import ServerCallContext

    context = ServerCallContext()
    task = await server.state.tasks.get(initial["remote_id"], context)
    task.status.state = p.TASK_STATE_COMPLETED
    task.artifacts[0].parts[0].text = "SIMULATED refreshed completion artifact"
    await server.state.tasks.save(task, context)
    await client.status("alice", initial["id"])
    exported = store.owned("alice", sid)
    assert exported["events"][-1]["task"]["state"] == "completed"
    assert (
        exported["events"][-1]["task"]["artifacts"][0]["text"]
        == "SIMULATED refreshed completion artifact"
    )

import httpx
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from simulated_specialist import make_simulator

from deep_agent.assistant import build_assistant
from deep_agent.config import Settings
from deep_agent.specialist import SpecialistClient
from deep_agent.store import Store


async def test_actual_graph_delegates_without_save_authority(tmp_path):
    settings = Settings(simulated=True, specialist_url="http://specialist")
    store = Store(tmp_path / "db")
    sid = store.create("alice")["id"]
    specialist = SpecialistClient(
        settings, store, transport=httpx.ASGITransport(app=make_simulator("http://specialist"))
    )

    offered = []
    prompts = []
    choices = []

    class Model(FakeMessagesListChatModel):
        async def _agenerate(self, messages, **kwargs):
            prompts.extend(message.content for message in messages)
            return await super()._agenerate(messages, **kwargs)

        def bind_tools(self, tools, **kwargs):
            choices.append(kwargs.get("tool_choice"))
            offered.extend(
                tool.name if hasattr(tool, "name") else tool.get("name", "") for tool in tools
            )
            return self

    model = Model(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "investigate_procurement",
                        "args": {"question": "Investigate GPU-A"},
                        "id": "call1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="The specialist returned an unresolved requirement. Inspect the artifact."
            ),
        ]
    )
    assistant = build_assistant(settings, store, specialist, None, model=model)
    lease = assistant.coordinator.reserve("alice", sid)
    events = [
        event
        async for event in assistant.run(
            "alice", sid, "Investigate GPU-A", "atlas", "2026-10-01T00:00:00Z", lease
        )
    ]
    assistant.coordinator.release(lease)
    assert any(
        event["kind"] == "task" and event["task"]["state"] == "completed" for event in events
    )
    assert choices == ["required", None]
    assert events[-1]["kind"] == "answer"
    assert store.owned("alice", sid)["events"][-1]["text"].startswith("The specialist")
    assert "approve" not in assistant.tool_names and "save" not in assistant.tool_names

    assert set(offered) == {
        "investigate_procurement",
        "procurement_task_status",
        "search_scifact",
        "answer_scifact",
    }

    assert any(
        "Selected project: atlas" in str(prompt) and "2026-10-01T00:00:00Z" in str(prompt)
        for prompt in prompts
    )


def test_model_timeout_honors_operator_deadline_without_retries(tmp_path):
    settings = Settings(timeout_seconds=90)
    assistant = build_assistant(settings, Store(tmp_path / "deadline-db"), None, None)
    assert assistant.model.request_timeout == settings.timeout_seconds
    assert assistant.model.max_retries == 0


async def test_no_tool_answer_is_rejected(tmp_path):
    import pytest

    class Model(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs):
            assert kwargs["tool_choice"] == "required"
            return self

    store = Store(tmp_path / "unsupported-db")
    sid = store.create("alice")["id"]
    assistant = build_assistant(
        Settings(),
        store,
        None,
        None,
        model=Model(responses=[AIMessage(content="I delegated the investigation.")]),
    )
    lease = assistant.coordinator.reserve("alice", sid)
    try:
        with pytest.raises(ValueError, match="No verified evidence"):
            async for _ in assistant.run(
                "alice", sid, "GPU-A", "atlas", "2026-10-01T00:00:00Z", lease
            ):
                pass
    finally:
        assistant.coordinator.release(lease)
    assert not any(e["kind"] == "answer" for e in store.owned("alice", sid)["events"])
    assert sid not in assistant.histories


async def test_failed_service_does_not_authorize_answer(tmp_path):
    import pytest

    class Model(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs):
            return self

    class Unavailable:
        async def answer(self, query):
            raise RuntimeError("offline")

    store = Store(tmp_path / "failed-service-db")
    sid = store.create("alice")["id"]
    model = Model(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    dict(
                        name="answer_scifact", args={"query": "claim"}, id="call1", type="tool_call"
                    )
                ],
            ),
            AIMessage(content="The claim is supported."),
        ]
    )
    assistant = build_assistant(Settings(), store, None, Unavailable(), model=model)
    lease = assistant.coordinator.reserve("alice", sid)
    try:
        with pytest.raises(ValueError, match="No verified evidence"):
            async for _ in assistant.run(
                "alice", sid, "claim", "atlas", "2026-10-01T00:00:00Z", lease
            ):
                pass
    finally:
        assistant.coordinator.release(lease)
    events = store.owned("alice", sid)["events"]
    assert any(e["kind"] == "error" for e in events)
    assert not any(e["kind"] == "answer" for e in events)

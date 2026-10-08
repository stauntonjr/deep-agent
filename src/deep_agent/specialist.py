"""Official A2A SDK adapter with fixed endpoints and application-owned identifiers."""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from time import perf_counter
from urllib.parse import urlsplit
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import a2a_pb2 as p
from google.protobuf.json_format import MessageToDict
from langsmith import trace

from .config import Settings
from .observability import client_for, context_for
from .store import Store


class BoundedTransport(httpx.AsyncBaseTransport):
    def __init__(self, inner, maximum=131072):
        self.inner = inner
        self.maximum = maximum

    async def handle_async_request(self, request):
        response = await self.inner.handle_async_request(request)
        data = bytearray()
        try:
            async for chunk in response.aiter_bytes():
                data.extend(chunk)
                if len(data) > self.maximum:
                    raise ValueError("specialist response exceeds limit")
        finally:
            await response.aclose()
        if 300 <= response.status_code < 400:
            raise ValueError("specialist redirects are forbidden")
        return httpx.Response(
            response.status_code, headers=response.headers, content=bytes(data), request=request
        )

    async def aclose(self):
        await self.inner.aclose()


class SpecialistClient:
    def __init__(self, settings: Settings, store: Store, transport=None):
        self.settings = settings
        self.store = store
        self.transport = transport
        self.trace_client = client_for(settings)

    @asynccontextmanager
    async def client(self):
        headers = {}
        if self.settings.service_token_file:
            from .app import read_private

            token = read_private(self.settings.service_token_file).strip()
            if not token or any(c.isspace() for c in token):
                raise ValueError("invalid service credential")
            headers["Authorization"] = "Bearer " + token
        transport = BoundedTransport(self.transport or httpx.AsyncHTTPTransport(retries=0))
        async with httpx.AsyncClient(
            timeout=20,
            transport=transport,
            follow_redirects=False,
            trust_env=False,
            headers=headers,
        ) as http:
            async with asyncio.timeout(30):
                card = await A2ACardResolver(http, self.settings.specialist_url).get_agent_card()
                origin = urlsplit(self.settings.specialist_url)
                for interface in card.supported_interfaces:
                    parsed = urlsplit(interface.url)
                    expected = (
                        self.settings.specialist_rpc_url
                        or self.settings.specialist_url.rstrip("/") + "/rpc"
                    )
                    if (
                        interface.url != expected
                        or (parsed.scheme, parsed.netloc) != (origin.scheme, origin.netloc)
                        or parsed.username
                        or parsed.password
                        or parsed.query
                        or parsed.fragment
                    ):
                        raise ValueError("agent interface is outside fixed endpoint")
                if not card.supported_interfaces or not any(
                    i.protocol_binding == "JSONRPC" and i.protocol_version == "1.0"
                    for i in card.supported_interfaces
                ):
                    raise ValueError("unsupported agent interface version")
                client = ClientFactory(
                    ClientConfig(
                        streaming=False,
                        polling=False,
                        httpx_client=http,
                        supported_protocol_bindings=["JSONRPC"],
                    )
                ).create(card)
                yield client

    @staticmethod
    def payload(task):
        state = p.TaskState.Name(task.status.state).removeprefix("TASK_STATE_").lower()
        if (
            state
            not in {
                "submitted",
                "working",
                "completed",
                "failed",
                "canceled",
                "input_required",
                "rejected",
                "auth_required",
            }
            or not task.id
            or len(task.id) > 256
        ):
            raise ValueError("invalid task result")
        artifacts = []
        for artifact in task.artifacts:
            text = "\n".join(part.text for part in artifact.parts if part.HasField("text"))
            if len(text) > 65536 or len(artifacts) >= 20:
                raise ValueError("artifact exceeds limit")
            # Remote URLs/data are not executable or clickable presentation authority.
            artifacts.append({"artifact_id": artifact.artifact_id[:256], "text": text})
        return {
            "remote_id": task.id,
            "context_id": task.context_id,
            "state": state,
            "artifacts": artifacts,
            "observations": MessageToDict(task.metadata).get("observations", {}),
        }

    async def investigate(
        self, viewer_id, session_id, question, project, as_of, *, on_event=None, correlation_id=None
    ):
        self.store.owned(viewer_id, session_id)
        cutoff = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        if cutoff.tzinfo is None:
            raise ValueError("aware cutoff required")
        record = self.store.put_task(
            viewer_id,
            session_id,
            {"state": "submitting", "artifacts": [], "simulated": self.settings.simulated},
        )
        correlation_id = correlation_id or str(uuid4())
        started = perf_counter()
        if on_event:
            await on_event(
                dict(
                    kind="a2a",
                    phase="request",
                    sender="DeepAgent",
                    receiver="Procurement specialist",
                    question=question,
                    project=project,
                    as_of=as_of,
                    correlation_id=correlation_id,
                    operation="SendMessage",
                )
            )
        try:
            with (
                context_for(self.settings, self.trace_client),
                trace(
                    "A2A SendMessage",
                    run_type="tool",
                    inputs={"question": question, "project": project, "as_of": as_of},
                    metadata={"correlation_id": correlation_id},
                ) as exchange,
            ):
                async with self.client() as client:
                    metadata = {"correlation_id": correlation_id}
                    if self.settings.langsmith_tracing:
                        metadata["parent_trace"] = exchange.to_headers()["langsmith-trace"]
                    request = p.SendMessageRequest(
                        message=p.Message(
                            message_id=str(uuid4()),
                            role=p.ROLE_USER,
                            metadata=metadata,
                            parts=[
                                p.Part(
                                    text=json.dumps(
                                        {"question": question, "project": project, "as_of": as_of}
                                    )
                                )
                            ],
                        )
                    )
                    async for event in client.send_message(request):
                        if not event.HasField("task"):
                            raise ValueError("specialist must return a task")
                        data = self.payload(event.task)
                        if on_event:
                            await on_event(
                                dict(
                                    kind="a2a",
                                    phase="response",
                                    sender="Procurement specialist",
                                    receiver="DeepAgent",
                                    correlation_id=correlation_id,
                                    remote_id=data["remote_id"],
                                    state=data["state"],
                                    elapsed_ms=round((perf_counter() - started) * 1000),
                                    observations=data.get("observations", {}),
                                )
                            )
                        exchange.end(
                            outputs={"state": data["state"], "remote_id": data["remote_id"]}
                        )
                        return self.store.put_task(
                            viewer_id,
                            session_id,
                            dict(data, simulated=self.settings.simulated),
                            record["id"],
                        )
                    raise ValueError("specialist returned no task")
        except BaseException:
            self.store.put_task(
                viewer_id,
                session_id,
                {"state": "unknown", "artifacts": [], "simulated": self.settings.simulated},
                record["id"],
            )
            raise

    async def status(self, viewer_id, task_id):
        record = self.store.task(viewer_id, task_id)
        if not record.get("remote_id"):
            return record
        async with self.client() as client:
            task = await client.get_task(p.GetTaskRequest(id=record["remote_id"], history_length=0))
            if task.id != record["remote_id"] or task.context_id != record["context_id"]:
                raise ValueError("task identity changed")
            updated = self.store.put_task(
                viewer_id,
                record["session_id"],
                dict(self.payload(task), simulated=self.settings.simulated),
                task_id,
            )
            self.store.event(viewer_id, record["session_id"], {"kind": "task", "task": updated})
            return updated

    async def cancel(self, viewer_id, task_id):
        record = self.store.task(viewer_id, task_id)
        if not record.get("remote_id"):
            return record
        try:
            async with self.client() as client:
                task = await client.cancel_task(p.CancelTaskRequest(id=record["remote_id"]))
                if task.id != record["remote_id"] or task.context_id != record["context_id"]:
                    raise ValueError("task identity changed")
                payload = dict(self.payload(task), simulated=self.settings.simulated)
        except Exception:
            payload = dict(record, cancellation="unknown")
        return self.store.put_task(viewer_id, record["session_id"], payload, task_id)

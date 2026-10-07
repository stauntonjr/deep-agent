"""Read-only A2A facade over procurement's admitted synthetic-corpus HTTP services."""

import asyncio
import hmac
import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from a2a.server.agent_execution import AgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import a2a_pb2 as p
from fastapi import FastAPI
from google.protobuf.json_format import MessageToDict
from starlette.responses import JSONResponse
from starlette.routing import Route

from .app import read_private
from .specialist import BoundedTransport


class ProcurementHTTP:
    def __init__(self, endpoint, transport=None):
        parsed = urlsplit(endpoint)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.path not in {"", "/"}
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("fixed procurement origin required")
        self.endpoint, self.transport = endpoint.rstrip("/"), transport

    async def investigate(self, project, item, as_of):
        async with (
            asyncio.timeout(30),
            httpx.AsyncClient(
                base_url=self.endpoint,
                timeout=10,
                trust_env=False,
                follow_redirects=False,
                headers={"Accept-Encoding": "identity"},
                transport=BoundedTransport(self.transport or httpx.AsyncHTTPTransport(retries=0)),
            ) as http,
        ):
            response = await http.get(
                "/api/corpus/investigate", params={"project": project, "item": item, "as_of": as_of}
            )
            response.raise_for_status()
            investigation = response.json()
            if (
                not isinstance(investigation, dict)
                or not isinstance(investigation.get("evidence"), list)
                or len(investigation["evidence"]) > 12
            ):
                raise ValueError("invalid procurement evidence")
            sources = []
            for ref in investigation["evidence"]:
                identifier = ref.get("evidence_id") if isinstance(ref, dict) else None
                if not isinstance(identifier, str) or not 0 < len(identifier) <= 512:
                    raise ValueError("invalid source identity")
                response = await http.get(
                    "/api/corpus/source", params={"project": project, "evidence_id": identifier}
                )
                response.raise_for_status()
                source = response.json()
                if not isinstance(source, dict):
                    raise ValueError("invalid source result")
                sources.append(source)
            result = {
                "data_boundary": "Admitted synthetic procurement corpus; actual domain services, not production procurement",
                "project": project,
                "item": item,
                "as_of": as_of,
                "investigation": investigation,
                "sources": sources,
                "authority": "read-only; no review/save/purchase",
            }
            text = json.dumps(result, ensure_ascii=False)
            if len(text.encode()) > 60000:
                raise ValueError("combined evidence exceeds artifact limit")
            return text


def build_bridge(origin, upstream, token, upstream_transport=None):
    if len(token) < 32 or any(c.isspace() for c in token):
        raise ValueError("private service token must have at least32 non-whitespace characters")
    parsed = urlsplit(origin)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "bridge"}
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise ValueError("bridge requires fixed loopback origin")
    service = ProcurementHTTP(upstream, upstream_transport)
    card = p.AgentCard(
        name="Procurement evidence specialist",
        description="Read-only investigation of admitted synthetic procurement corpus",
        version="0.1.0",
        supported_interfaces=[
            p.AgentInterface(
                url=origin.rstrip("/") + "/rpc", protocol_binding="JSONRPC", protocol_version="1.0"
            )
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            p.AgentSkill(
                id="investigate",
                name="Investigate procurement evidence",
                description="Read scoped quantities and original sources; no review or save",
                tags=["procurement", "read-only", "synthetic-corpus"],
            )
        ],
    )

    class Executor(AgentExecutor):
        async def execute(self, context, event_queue):
            try:
                if context.message is None:
                    raise ValueError("message required")
                parts = context.message.parts
                if len(parts) != 1 or not parts[0].HasField("text"):
                    raise ValueError("one scoped request required")
                values = json.loads(parts[0].text)
                if (
                    not isinstance(values, dict)
                    or set(values) != {"question", "project", "as_of"}
                    or not all(isinstance(v, str) for v in values.values())
                ):
                    raise ValueError("exact scoped fields required")
                if len(values["question"]) > 4096 or values["project"] not in {
                    "atlas",
                    "borealis",
                    "cinder",
                    "delta",
                }:
                    raise ValueError("invalid scope")
                cutoff = datetime.fromisoformat(values["as_of"].replace("Z", "+00:00"))
                if cutoff.tzinfo is None:
                    raise ValueError("timezone-aware cutoff required")
                items = set(re.findall(r"\b[A-Z][A-Z0-9]*-[A-Z0-9]+\b", values["question"]))
                if len(items) != 1:
                    state, text = (
                        p.TASK_STATE_INPUT_REQUIRED,
                        "Provide exactly one explicit canonical item, such as GPU-A. No evidence was queried.",
                    )
                else:
                    text = await service.investigate(
                        values["project"], items.pop(), values["as_of"]
                    )
                    state = p.TASK_STATE_COMPLETED
            except Exception:
                state, text = (
                    p.TASK_STATE_FAILED,
                    "Procurement request failed validation or service access. No substitute evidence produced; no review/save occurred.",
                )
            await event_queue.enqueue_event(
                p.Task(
                    id=context.task_id,
                    context_id=context.context_id,
                    status=p.TaskStatus(state=state),
                    artifacts=[
                        p.Artifact(artifact_id="procurement-evidence", parts=[p.Part(text=text)])
                    ],
                )
            )

        async def cancel(self, context, event_queue):
            # Read-only synchronous task outcomes remain owned by SDK task storage.
            await event_queue.enqueue_event(
                p.Task(
                    id=context.task_id,
                    context_id=context.context_id,
                    status=p.TaskStatus(state=p.TASK_STATE_CANCELED),
                )
            )

    handler = DefaultRequestHandler(Executor(), InMemoryTaskStore(), card)

    async def discovery(request):
        return JSONResponse(MessageToDict(card))

    app = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        routes=[
            Route("/.well-known/agent-card.json", discovery),
            *create_jsonrpc_routes(handler, "/rpc"),
        ],
    )

    @app.middleware("http")
    async def boundary(request, call_next):
        if request.headers.get("host") != urlsplit(origin).netloc:
            return JSONResponse({"error": "invalid host"}, status_code=400)
        provided = request.headers.get("authorization", "")
        if not hmac.compare_digest(provided.encode(), ("Bearer " + token).encode()):
            return JSONResponse({"error": "service authentication required"}, status_code=401)
        if request.method == "POST":
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 16384:
                    return JSONResponse({"error": "request too large"}, status_code=413)
            request._body = bytes(body)
        return await call_next(request)

    return app


def main():
    import uvicorn

    token = read_private(Path(os.environ["DEEPAGENT_SERVICE_TOKEN_FILE"])).strip()
    uvicorn.run(
        build_bridge(
            "http://127.0.0.1:8101",
            os.getenv("DEEPAGENT_PROCUREMENT_URL", "http://127.0.0.1:8092"),
            token,
        ),
        host="127.0.0.1",
        port=8101,
        access_log=False,
    )


if __name__ == "__main__":
    main()

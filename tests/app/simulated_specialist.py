"""Test-only A2A transport fixture, not a procurement implementation."""

from a2a.server.agent_execution import AgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import a2a_pb2 as p
from fastapi import FastAPI
from google.protobuf.json_format import MessageToDict
from starlette.responses import JSONResponse
from starlette.routing import Route


def make_simulator(
    url, state="completed", text="SIMULATED: requirement unresolved; source BOM!C2."
):
    card = p.AgentCard(
        name="Simulated procurement specialist",
        description="Local protocol fixture only",
        version="1.0",
        supported_interfaces=[
            p.AgentInterface(url=url + "/rpc", protocol_binding="JSONRPC", protocol_version="1.0")
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            p.AgentSkill(
                id="investigate",
                name="Simulated investigation",
                description="Test protocol lifecycle",
                tags=["simulation"],
            )
        ],
    )
    target = getattr(p, "TASK_STATE_" + state.upper())

    class Executor(AgentExecutor):
        async def execute(self, context, event_queue):
            await event_queue.enqueue_event(
                p.Task(
                    id=context.task_id,
                    context_id=context.context_id,
                    status=p.TaskStatus(state=target),
                    artifacts=[p.Artifact(artifact_id="brief", parts=[p.Part(text=text)])],
                )
            )

        async def cancel(self, context, event_queue):
            await event_queue.enqueue_event(
                p.Task(
                    id=context.task_id,
                    context_id=context.context_id,
                    status=p.TaskStatus(state=p.TASK_STATE_CANCELED),
                )
            )

    tasks = InMemoryTaskStore()
    handler = DefaultRequestHandler(Executor(), tasks, card)

    async def discovery(request):
        return JSONResponse(MessageToDict(card))

    app = FastAPI(
        routes=[
            Route("/.well-known/agent-card.json", discovery),
            *create_jsonrpc_routes(handler, "/rpc"),
        ]
    )
    app.state.calls = []
    app.state.tasks = tasks

    @app.middleware("http")
    async def audit(request, call_next):
        if request.method == "POST":
            payload = await request.json()
            app.state.calls.append(payload.get("method"))
        return await call_next(request)

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(make_simulator("http://127.0.0.1:8101"), host="127.0.0.1", port=8101)

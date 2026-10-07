"""Authenticated HTTP boundary. Human review is unavailable pending real integration."""

import asyncio
import json
import stat
from pathlib import Path
from typing import Annotated

import bcrypt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, ConfigDict, Field

from .config import Settings
from .store import Store


class Empty(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Prompt(Empty):
    prompt: str = Field(min_length=1, max_length=4096)
    project: str = Field(default="atlas", pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    as_of: str = Field(default="2026-10-01T00:00:00Z", max_length=64)


def read_private(path: Path) -> str:
    import os

    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_mode & 0o077
            or info.st_uid != os.geteuid()
            or info.st_size > 16384
        ):
            raise ValueError("credential file must be an owned private regular file")
        with os.fdopen(fd, "r", closefd=False) as handle:
            return handle.read()
    finally:
        os.close(fd)


def create_app(settings: Settings, store: Store, assistant):
    # Fail before serving if the credential contract cannot be fulfilled.
    def credentials():
        result = {}
        for line in read_private(settings.credentials_file).splitlines():
            name, hashed = line.split(":", 1)
            if not name or name in result or not hashed.startswith(("$2a$", "$2b$", "$2y$")):
                raise ValueError("invalid credential record")
            result[name] = hashed.encode()
        if not result:
            raise ValueError("empty credential file")
        return result

    credentials()
    dummy = bcrypt.hashpw(b"not-a-password", bcrypt.gensalt())
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    basic = HTTPBasic()

    async def viewer(request: Request, auth: Annotated[HTTPBasicCredentials, Depends(basic)]):
        try:
            users = credentials()  # Revocation takes effect on each request.
            password = auth.password.encode()
            hashed = users.get(auth.username, dummy)
            accepted = len(password) <= 72 and await asyncio.to_thread(
                bcrypt.checkpw, password, hashed
            )
        except (OSError, ValueError):
            raise HTTPException(503, "Authentication configuration unavailable") from None
        if not accepted or auth.username not in users:
            raise HTTPException(401, "Invalid credentials", headers={"WWW-Authenticate": "Basic"})
        if request.method not in {"GET", "HEAD"}:
            if request.headers.get("origin") not in {None, settings.origin.rstrip("/")}:
                raise HTTPException(403, "Origin rejected")
            if request.headers.get("sec-fetch-site") == "cross-site":
                raise HTTPException(403, "Cross-site request rejected")
        return auth.username

    @app.middleware("http")
    async def boundaries(request, call_next):
        if request.headers.get("host") != settings.origin.split("://", 1)[1].rstrip("/"):
            return PlainTextResponse("Host rejected", status_code=403)
        if request.method not in {"GET", "HEAD"}:
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 16384:
                    return PlainTextResponse("Request too large", status_code=413)
            request._body = bytes(body)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        )
        return response

    @app.exception_handler(KeyError)
    async def missing(request, error):
        return PlainTextResponse("Not found", status_code=404)

    @app.get("/healthz")
    async def health(identity=Depends(viewer)):
        return {
            "status": "ok",
            "simulated": settings.simulated,
            "procurement_review": "pending integration",
        }

    @app.get("/api/sessions")
    async def sessions(identity=Depends(viewer)):
        return store.sessions(identity)

    @app.post("/api/sessions", status_code=201)
    async def new(body: Empty, identity=Depends(viewer)):
        return store.create(identity)

    @app.get("/api/sessions/{sid}")
    async def session(sid: str, identity=Depends(viewer)):
        return store.owned(identity, sid)

    @app.delete("/api/sessions/{sid}")
    async def delete(sid: str, identity=Depends(viewer)):
        if assistant and assistant.coordinator.busy_session(sid):
            raise HTTPException(409, "Cancel the active run before resetting")
        store.delete(identity, sid)
        if assistant:
            assistant.histories.pop(sid, None)
        return {"deleted": True}

    @app.get("/api/sessions/{sid}/download")
    async def download(sid: str, identity=Depends(viewer)):
        data = store.owned(identity, sid)
        return PlainTextResponse(
            json.dumps(data, indent=2),
            headers={"Content-Disposition": 'attachment; filename="evidence-brief.json"'},
        )

    @app.get("/api/tasks/{tid}")
    async def task(tid: str, identity=Depends(viewer)):
        if assistant:
            return await assistant.specialist.status(identity, tid)
        return store.task(identity, tid)

    @app.post("/api/tasks/{tid}/review")
    async def review(tid: str, body: Empty, identity=Depends(viewer)):
        store.task(identity, tid)
        raise HTTPException(409, "Human review awaits the accepted procurement integration")

    @app.post("/api/sessions/{sid}/run")
    async def run(sid: str, body: Prompt, request: Request, identity=Depends(viewer)):
        store.owned(identity, sid)
        if not assistant:
            raise HTTPException(503, "Assistant is unavailable")
        if not body.prompt.strip():
            raise HTTPException(422, "Prompt must not be blank")
        lease = assistant.coordinator.reserve(identity, sid)
        if lease is None:
            raise HTTPException(429, "Run queue is full or you already have a run")

        async def events():
            try:
                async with asyncio.timeout(settings.timeout_seconds):
                    async for event in assistant.run(
                        identity, sid, body.prompt, body.project, body.as_of, lease
                    ):
                        if await request.is_disconnected():
                            return
                        yield json.dumps(event) + "\n"
            except TimeoutError:
                event = {
                    "kind": "error",
                    "text": "Run deadline reached; remote outcome may be unknown.",
                }
                store.event(identity, sid, event)
                yield json.dumps(event) + "\n"
            except Exception:
                event = {
                    "kind": "error",
                    "text": "Run failed. No automatic retry; inspect task history before retrying.",
                }
                store.event(identity, sid, event)
                yield json.dumps(event) + "\n"
            finally:
                assistant.coordinator.release(lease)

        return StreamingResponse(events(), media_type="application/x-ndjson")

    web = Path(__file__).parent / "web"

    @app.get("/")
    async def index(identity=Depends(viewer)):
        return FileResponse(web / "index.html")

    @app.get("/app.js")
    async def script(identity=Depends(viewer)):
        return FileResponse(web / "app.js")

    @app.get("/app.css")
    async def style(identity=Depends(viewer)):
        return FileResponse(web / "app.css")

    return app

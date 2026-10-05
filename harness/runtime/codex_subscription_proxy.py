"""Credential-isolated relay for Pi's ChatGPT Pro/Codex subscription provider."""

from __future__ import annotations

import base64
import http.client
import json
import os
import re
import secrets
import stat
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

CODEX_HOST = "chatgpt.com"
CODEX_RESPONSES_PATH = "/backend-api/codex/responses"
LOCAL_CODEX_RESPONSES_PATH = CODEX_RESPONSES_PATH
CONTROL_MODEL = "gpt-5.6-sol"
CONTROL_REASONING_EFFORT = "medium"
JWT_CLAIM_PATH = "https://api.openai.com/auth"
MAXIMUM_CODEX_AUTH_BYTES = 64 * 1024
MAXIMUM_ACCESS_TOKEN_CHARACTERS = 32 * 1024
MAXIMUM_ACCOUNT_ID_CHARACTERS = 256
JWT_TOKEN = re.compile(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*\Z")
ACCOUNT_ID = re.compile(r"[A-Za-z0-9._:-]+\Z")


class SubscriptionProxyError(ValueError):
    """A fail-closed subscription credential, relay, or budget error."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SubscriptionProxyError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _validate_credential_headers(access_token: str, account_id: str) -> None:
    if (
        not 1 <= len(access_token) <= MAXIMUM_ACCESS_TOKEN_CHARACTERS
        or JWT_TOKEN.fullmatch(access_token) is None
    ):
        raise SubscriptionProxyError("Codex subscription access token is not header-safe")
    if (
        not 1 <= len(account_id) <= MAXIMUM_ACCOUNT_ID_CHARACTERS
        or ACCOUNT_ID.fullmatch(account_id) is None
    ):
        raise SubscriptionProxyError("Codex subscription account identity is not header-safe")


@dataclass(frozen=True)
class CodexSubscriptionCredential:
    access_token: str
    account_id: str
    expires_at: int


@dataclass(frozen=True)
class SubscriptionBudget:
    maximum_requests: int
    maximum_request_bytes: int
    upstream_timeout_seconds: int

    def validate(self) -> None:
        values = (
            self.maximum_requests,
            self.maximum_request_bytes,
            self.upstream_timeout_seconds,
        )
        if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
            raise SubscriptionProxyError("subscription budget values must be integers")
        if not 1 <= self.maximum_requests <= 100:
            raise SubscriptionProxyError("subscription request bound is invalid")
        if not 1024 <= self.maximum_request_bytes <= 8 * 1024 * 1024:
            raise SubscriptionProxyError("subscription request-byte bound is invalid")
        if not 30 <= self.upstream_timeout_seconds <= 900:
            raise SubscriptionProxyError("subscription upstream timeout is invalid")


@dataclass
class _BudgetState:
    budget: SubscriptionBudget
    requests: int = 0
    request_bytes: int = 0

    def reserve(self, body_bytes: int) -> None:
        if self.requests + 1 > self.budget.maximum_requests:
            raise SubscriptionProxyError("subscription request-count budget exhausted")
        if self.request_bytes + body_bytes > self.budget.maximum_request_bytes:
            raise SubscriptionProxyError("subscription request-byte budget exhausted")
        self.requests += 1
        self.request_bytes += body_bytes


@dataclass(frozen=True)
class SubscriptionProxyMetrics:
    requests: int
    request_bytes: int


def _base64url(value: dict[str, Any]) -> str:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def create_model_canary_token() -> str:
    """Create a per-process non-secret JWT for Pi's local account parser."""
    header = _base64url({"alg": "none", "typ": "JWT"})
    payload = _base64url(
        {
            "exp": int(time.time()) + 3600,
            "nonce": secrets.token_urlsafe(32),
            JWT_CLAIM_PATH: {"chatgpt_account_id": "harness-canary"},
        }
    )
    return f"{header}.{payload}."


def _decode_jwt_claims(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise SubscriptionProxyError("Codex subscription access token is not a JWT")
    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(
            base64.urlsafe_b64decode(payload),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (ValueError, json.JSONDecodeError, UnicodeError) as exc:
        raise SubscriptionProxyError("Codex subscription access token is malformed") from exc
    if not isinstance(claims, dict):
        raise SubscriptionProxyError("Codex subscription access token claims are invalid")
    return claims


def load_codex_subscription(
    path: Path,
    *,
    minimum_lifetime_seconds: int = 3600,
) -> CodexSubscriptionCredential:
    """Load a current ChatGPT-authenticated Codex credential without printing it."""
    if (
        isinstance(minimum_lifetime_seconds, bool)
        or not isinstance(minimum_lifetime_seconds, int)
        or not 60 <= minimum_lifetime_seconds <= 86400
    ):
        raise SubscriptionProxyError("minimum subscription lifetime is invalid")
    target = Path(os.path.abspath(path))
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    file_flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    directory_descriptor: int | None = None
    file_descriptor: int | None = None
    try:
        directory_descriptor = os.open(target.anchor, directory_flags)
        for component in target.parent.parts[1:]:
            next_descriptor = os.open(
                component,
                directory_flags,
                dir_fd=directory_descriptor,
            )
            os.close(directory_descriptor)
            directory_descriptor = next_descriptor
        metadata = os.stat(
            target.name,
            dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
        file_descriptor = os.open(target.name, file_flags, dir_fd=directory_descriptor)
        opened = os.fstat(file_descriptor)
    except OSError as exc:
        raise SubscriptionProxyError("Codex subscription login is unavailable") from exc
    try:
        if (
            not stat.S_ISREG(metadata.st_mode)
            or not stat.S_ISREG(opened.st_mode)
            or (metadata.st_dev, metadata.st_ino) != (opened.st_dev, opened.st_ino)
            or metadata.st_size < 2
            or metadata.st_size > MAXIMUM_CODEX_AUTH_BYTES
            or metadata.st_mode & 0o077
        ):
            raise SubscriptionProxyError("Codex auth file must be a private bounded regular file")
        chunks: list[bytes] = []
        observed = 0
        while True:
            chunk = os.read(
                file_descriptor,
                min(65536, MAXIMUM_CODEX_AUTH_BYTES + 1 - observed),
            )
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
            if observed > MAXIMUM_CODEX_AUTH_BYTES:
                raise SubscriptionProxyError("Codex auth file exceeds its bound")
        after = os.fstat(file_descriptor)
        if (
            after.st_size != metadata.st_size
            or after.st_mtime_ns != metadata.st_mtime_ns
            or after.st_ctime_ns != metadata.st_ctime_ns
            or observed != metadata.st_size
        ):
            raise SubscriptionProxyError("Codex auth file changed while reading")
        raw = b"".join(chunks)
        payload = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    except (OSError, json.JSONDecodeError, RecursionError) as exc:
        raise SubscriptionProxyError("Codex auth file is unreadable") from exc
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        if directory_descriptor is not None:
            os.close(directory_descriptor)
    if not isinstance(payload, dict) or payload.get("auth_mode") != "chatgpt":
        raise SubscriptionProxyError("Codex is not logged in with ChatGPT")
    if payload.get("OPENAI_API_KEY") not in (None, ""):
        raise SubscriptionProxyError("API-key Codex auth is prohibited for this control")
    tokens = payload.get("tokens")
    if not isinstance(tokens, dict):
        raise SubscriptionProxyError("Codex ChatGPT token set is missing")
    access = tokens.get("access_token")
    account_id = tokens.get("account_id")
    if (
        not isinstance(access, str)
        or not access
        or not isinstance(account_id, str)
        or not account_id
    ):
        raise SubscriptionProxyError("Codex ChatGPT token set is incomplete")
    _validate_credential_headers(access, account_id)
    claims = _decode_jwt_claims(access)
    auth_claim = claims.get(JWT_CLAIM_PATH)
    if not isinstance(auth_claim, dict):
        raise SubscriptionProxyError("Codex ChatGPT token auth claim is invalid")
    claim_account = auth_claim.get("chatgpt_account_id")
    expires = claims.get("exp")
    if claim_account != account_id or isinstance(expires, bool) or not isinstance(expires, int):
        raise SubscriptionProxyError("Codex ChatGPT token identity is inconsistent")
    if expires - int(time.time()) < minimum_lifetime_seconds:
        raise SubscriptionProxyError("Codex ChatGPT login expires too soon; refresh with Codex")
    return CodexSubscriptionCredential(
        access_token=access,
        account_id=account_id,
        expires_at=expires,
    )


class CodexSubscriptionProxy:
    """A loopback relay that keeps ChatGPT OAuth outside the model sandbox."""

    def __init__(
        self,
        *,
        credential: CodexSubscriptionCredential,
        budget: SubscriptionBudget,
    ) -> None:
        budget.validate()
        if (
            not isinstance(credential.access_token, str)
            or not credential.access_token
            or not isinstance(credential.account_id, str)
            or not credential.account_id
            or isinstance(credential.expires_at, bool)
            or not isinstance(credential.expires_at, int)
            or credential.expires_at <= int(time.time())
        ):
            raise SubscriptionProxyError("Codex subscription credential is invalid")
        _validate_credential_headers(credential.access_token, credential.account_id)
        claims = _decode_jwt_claims(credential.access_token)
        auth_claim = claims.get(JWT_CLAIM_PATH)
        if not isinstance(auth_claim, dict):
            raise SubscriptionProxyError("Codex subscription credential auth claim is invalid")
        claim_account = auth_claim.get("chatgpt_account_id")
        claim_expiry = claims.get("exp")
        if claim_account != credential.account_id or claim_expiry != credential.expires_at:
            raise SubscriptionProxyError("Codex subscription credential identity is inconsistent")
        self._credential = credential
        self._model_token = create_model_canary_token()
        self._state = _BudgetState(budget)
        self._lock = threading.Lock()
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def model_token(self) -> str:
        """Return the per-relay canary bearer; it is not an API or OAuth key."""
        return self._model_token

    @property
    def base_url(self) -> str:
        if self._server is None:
            raise SubscriptionProxyError("subscription relay has not started")
        return f"http://127.0.0.1:{self._server.server_port}/backend-api"

    @property
    def metrics(self) -> SubscriptionProxyMetrics:
        with self._lock:
            return SubscriptionProxyMetrics(
                requests=self._state.requests,
                request_bytes=self._state.request_bytes,
            )

    def start(self) -> None:
        if self._server is not None:
            raise SubscriptionProxyError("subscription relay is already running")
        owner = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, _format: str, *_args: Any) -> None:
                return

            def _json_error(self, status: int, message: str) -> None:
                body = json.dumps(
                    {"error": {"type": "subscription_relay_rejection", "message": message}},
                    separators=(",", ":"),
                ).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(body)
                self.close_connection = True

            def do_POST(self) -> None:  # noqa: N802
                if self.path != LOCAL_CODEX_RESPONSES_PATH:
                    self._json_error(404, "only the Codex Responses endpoint is available")
                    return
                if not secrets.compare_digest(
                    self.headers.get("Authorization", ""),
                    f"Bearer {owner._model_token}",
                ) or not secrets.compare_digest(
                    self.headers.get("chatgpt-account-id", ""),
                    "harness-canary",
                ):
                    self._json_error(401, "subscription relay canary authentication failed")
                    return
                if self.headers.get("Transfer-Encoding"):
                    self._json_error(400, "streamed request bodies are not accepted")
                    return
                try:
                    length = int(self.headers.get("Content-Length") or "")
                except ValueError:
                    self._json_error(400, "a valid Content-Length is required")
                    return
                if length < 1 or length > owner._state.budget.maximum_request_bytes:
                    self._json_error(413, "request body exceeds the subscription bound")
                    return
                body = self.rfile.read(length)
                if len(body) != length:
                    self._json_error(400, "request body ended early")
                    return
                try:
                    with owner._lock:
                        owner._state.reserve(len(body))
                except SubscriptionProxyError as exc:
                    self._json_error(429, str(exc))
                    return
                headers = {
                    "Authorization": f"Bearer {owner._credential.access_token}",
                    "chatgpt-account-id": owner._credential.account_id,
                    "originator": "pi",
                    "User-Agent": "agentic-engineering-harness-control/1",
                }
                for name in (
                    "Accept",
                    "Content-Type",
                    "Content-Encoding",
                    "OpenAI-Beta",
                    "session-id",
                    "x-client-request-id",
                ):
                    value = self.headers.get(name)
                    if value:
                        headers[name] = value
                upstream = http.client.HTTPSConnection(
                    CODEX_HOST,
                    timeout=owner._state.budget.upstream_timeout_seconds,
                )
                response_started = False
                try:
                    upstream.request(
                        "POST",
                        CODEX_RESPONSES_PATH,
                        body=body,
                        headers=headers,
                    )
                    response = upstream.getresponse()
                    self.send_response(response.status)
                    for name in ("Content-Type", "retry-after", "retry-after-ms"):
                        value = response.getheader(name)
                        if value:
                            self.send_header(name, value)
                    self.send_header("Connection", "close")
                    self.end_headers()
                    response_started = True
                    while True:
                        chunk = response.read(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        self.wfile.flush()
                except (OSError, ValueError, http.client.HTTPException):
                    if not response_started:
                        self._json_error(502, "Codex subscription upstream request failed")
                finally:
                    upstream.close()
                    self.close_connection = True

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def close(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._server = None
        self._thread = None


@contextmanager
def codex_subscription_proxy(
    *,
    credential: CodexSubscriptionCredential,
    budget: SubscriptionBudget,
) -> Iterator[CodexSubscriptionProxy]:
    proxy = CodexSubscriptionProxy(credential=credential, budget=budget)
    proxy.start()
    try:
        yield proxy
    finally:
        proxy.close()

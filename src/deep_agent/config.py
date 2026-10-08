"""Validated operator configuration; endpoint authority never comes from a model."""

from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, model_validator


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    credentials_file: Path = Path("/run/secrets/deepagent-users")
    database: Path = Path("/tmp/deepagent.sqlite")
    origin: str = "http://127.0.0.1:8100"
    production: bool = False
    simulated: bool = False
    model_url: str = "http://127.0.0.1:8000/v1"
    model: str = "nvidia/Qwen3.6-35B-A3B-NVFP4"
    specialist_url: str = "http://127.0.0.1:8101"
    specialist_rpc_url: str | None = None
    scifact_url: str = "http://127.0.0.1:8091/mcp"
    service_token_file: Path | None = None
    timeout_seconds: float = 300
    langsmith_tracing: bool = False
    langsmith_project: str = "deepagent-showcase"
    langsmith_key_file: Path | None = None

    @model_validator(mode="after")
    def validate_settings(self):
        if self.production and self.simulated:
            raise ValueError("simulation is forbidden in production")
        for value in (self.origin, self.model_url, self.specialist_url, self.scifact_url):
            parsed = urlsplit(value)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError("invalid fixed endpoint")
        if urlsplit(self.origin).path not in {"", "/"}:
            raise ValueError("origin must not contain a path")
        if self.production and not self.origin.startswith("https://"):
            raise ValueError("production requires HTTPS origin")
        if not 0 < self.timeout_seconds <= 300:
            raise ValueError("deadline must be in (0,300] seconds")
        return self

    @classmethod
    def from_env(cls):
        import os

        mapping = {
            "credentials_file": "DEEPAGENT_USERS_FILE",
            "database": "DEEPAGENT_DATABASE",
            "origin": "DEEPAGENT_ORIGIN",
            "model_url": "DEEPAGENT_MODEL_URL",
            "model": "DEEPAGENT_MODEL",
            "specialist_url": "DEEPAGENT_SPECIALIST_URL",
            "specialist_rpc_url": "DEEPAGENT_SPECIALIST_RPC_URL",
            "scifact_url": "DEEPAGENT_SCIFACT_URL",
            "service_token_file": "DEEPAGENT_SERVICE_TOKEN_FILE",
            "langsmith_project": "DEEPAGENT_LANGSMITH_PROJECT",
            "langsmith_key_file": "DEEPAGENT_LANGSMITH_KEY_FILE",
        }
        values: dict[str, object] = {
            key: os.environ[name] for key, name in mapping.items() if name in os.environ
        }
        values.update(
            production=os.getenv("DEEPAGENT_PRODUCTION") == "1",
            simulated=os.getenv("DEEPAGENT_SIMULATED") == "1",
            langsmith_tracing=os.getenv("DEEPAGENT_LANGSMITH_TRACING") == "1",
        )
        return cls.model_validate(values)

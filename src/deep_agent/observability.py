"""Opt-in maintained LangSmith tracing; credentials never enter event records."""

import os
from datetime import datetime, timezone

from langsmith import Client, tracing_context


def client_for(settings):
    if not settings.langsmith_tracing:
        return None
    key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if settings.langsmith_key_file:
        from .app import read_private

        key = read_private(settings.langsmith_key_file).strip()
    if not key:
        raise ValueError("LangSmith opt-in requires a private key file or LANGSMITH_API_KEY")
    return Client(api_key=key)


def context_for(settings, client=None, parent=None):
    return tracing_context(
        enabled=settings.langsmith_tracing,
        project_name=settings.langsmith_project,
        client=client,
        parent=parent,
    )


def stamp(event, correlation_id):
    return dict(
        event,
        correlation_id=correlation_id,
        observed_at=datetime.now(timezone.utc).isoformat(),
    )

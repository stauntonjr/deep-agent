"""Loopback development server; production bind is selected explicitly by operator."""

import os

import uvicorn

from .app import create_app
from .assistant import build_assistant
from .config import Settings
from .scifact import SciFactClient
from .specialist import SpecialistClient
from .store import Store


def main():
    settings = Settings.from_env()
    store = Store(settings.database)
    assistant = build_assistant(
        settings, store, SpecialistClient(settings, store), SciFactClient(settings.scifact_url)
    )
    uvicorn.run(
        create_app(settings, store, assistant),
        host=os.getenv("DEEPAGENT_BIND", "127.0.0.1"),
        port=8100,
        access_log=False,
    )


if __name__ == "__main__":
    main()

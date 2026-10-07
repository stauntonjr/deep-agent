import os

import bcrypt
from fastapi.testclient import TestClient

from deep_agent.app import create_app
from deep_agent.config import Settings
from deep_agent.store import Store


def test_browser_assets_and_safe_contract(tmp_path):
    users = tmp_path / "users"
    users.write_text("alice:" + bcrypt.hashpw(b"pass", bcrypt.gensalt(rounds=4)).decode())
    os.chmod(users, 0o600)
    settings = Settings(credentials_file=users, origin="http://testserver", simulated=True)
    with TestClient(create_app(settings, Store(tmp_path / "db"), None)) as client:
        response = client.get("/", auth=("alice", "pass"))
        assert response.status_code == 200
        assert "Evidence assistant" in response.text
        assert client.get("/app.js", auth=("alice", "pass")).status_code == 200
        assert "frame-ancestors" in response.headers["Content-Security-Policy"]
        assert client.get("/app.js").status_code == 401

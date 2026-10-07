import os

import bcrypt
import pytest
from fastapi.testclient import TestClient

from deep_agent.app import create_app
from deep_agent.config import Settings
from deep_agent.store import Store


@pytest.fixture
def client(tmp_path):
    credentials = tmp_path / "users"
    credentials.write_text(
        "\n".join(
            name + ":" + bcrypt.hashpw(b"pass", bcrypt.gensalt(rounds=4)).decode()
            for name in ["alice", "bob"]
        )
    )
    os.chmod(credentials, 0o600)
    settings = Settings(
        credentials_file=credentials,
        database=tmp_path / "db",
        origin="http://testserver",
        simulated=True,
    )
    with TestClient(create_app(settings, Store(settings.database), None)) as client:
        yield client


def test_no_auth_or_wrong_password_is_rejected(client):
    assert client.get("/api/sessions").status_code == 401
    assert client.get("/api/sessions", auth=("alice", "wrong")).status_code == 401


def test_owned_sessions_and_artifacts_are_not_shared(client):
    response = client.post("/api/sessions", auth=("alice", "pass"), json={})
    assert response.status_code == 201
    sid = response.json()["id"]
    assert client.get("/api/sessions/" + sid, auth=("bob", "pass")).status_code == 404
    assert client.get("/api/sessions", auth=("bob", "pass")).json() == []
    assert client.get("/api/sessions/" + sid + "/download", auth=("bob", "pass")).status_code == 404
    assert client.delete("/api/sessions/" + sid, auth=("bob", "pass")).status_code == 404


def test_identity_and_foreign_origin_cannot_grant_authority(client):
    assert (
        client.post("/api/sessions", auth=("alice", "pass"), json={"viewer_id": "bob"}).status_code
        == 422
    )
    assert (
        client.post(
            "/api/sessions",
            auth=("alice", "pass"),
            headers={"Origin": "https://evil.test"},
            json={},
        ).status_code
        == 403
    )
    assert client.get("/api/sessions", headers={"X-Demo-Viewer": "alice"}).status_code == 401


def test_credentials_must_be_private_and_simulation_not_production(tmp_path):
    credentials = tmp_path / "users"
    credentials.write_text("alice:bad")
    os.chmod(credentials, 0o644)
    with pytest.raises(ValueError):
        create_app(
            Settings(credentials_file=credentials, database=tmp_path / "db"),
            Store(tmp_path / "db"),
            None,
        )
    with pytest.raises(ValueError):
        Settings(production=True, simulated=True)


def test_foreign_stream_and_review_cannot_be_accessed(client):
    sid = client.post("/api/sessions", auth=("alice", "pass"), json={}).json()["id"]
    assert (
        client.post(
            "/api/sessions/" + sid + "/run", auth=("bob", "pass"), json={"prompt": "test"}
        ).status_code
        == 404
    )
    assert (
        client.post("/api/tasks/unknown/review", auth=("bob", "pass"), json={}).status_code == 404
    )
    assert (
        client.post(
            "/api/sessions",
            auth=("alice", "pass"),
            headers={"Sec-Fetch-Site": "cross-site"},
            json={},
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/api/sessions", auth=("alice", "pass"), headers={"Host": "evil.test"}
        ).status_code
        == 403
    )


def test_chunked_oversized_request_is_rejected_before_parsing(client):
    def chunks():
        yield b'{"irrelevant":"'
        yield b"x" * 17000
        yield b'"}'

    response = client.post(
        "/api/sessions",
        auth=("alice", "pass"),
        headers={"Content-Type": "application/json"},
        content=chunks(),
    )
    assert response.status_code == 413

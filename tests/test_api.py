"""Integration tests use PostgreSQL and rollback every test's transaction."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database import get_db, settings
from app.main import app

@pytest.fixture()
def client():
    engine = create_engine(settings.database_url)
    # Requires a separately created, seeded test database; see README.
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    def override():
        yield session
    app.dependency_overrides[get_db] = override
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()

def test_seed_and_details(client):
    rows = client.get("/api/criminals/").json()
    assert len(rows) >= 5
    assert any(c["name"] is None for c in rows)
    assert all(1 <= c["difficulty"] <= 10 for c in rows)
    assert client.get("/api/criminals/1/").json()["id"] == 1
    assert len(client.get("/api/hunts/").json()) >= 10

@pytest.mark.parametrize("sort,reverse", [("reward", False), ("-reward", True)])
def test_sort(client, sort, reverse):
    rows = client.get("/api/criminals/", params={"sort": sort}).json()
    rewards = [float(c["reward"]) for c in rows]
    assert rewards == sorted(rewards, reverse=reverse)

def test_combined_filters(client):
    response = client.get("/api/criminals/", params=dict(min_reward=5000, max_reward=20000,
        armed="true", has_crew="false", escape_master="true", sort="-reward"))
    assert response.status_code == 200
    rows = response.json()
    assert [c["nickname"] for c in rows] == ["Night Falcon"]

def test_zero_and_false_filters(client):
    rows = client.get("/api/criminals/?min_reward=0&armed=false").json()
    assert len(rows) == 2
    assert all(c["armed"] is False for c in rows)
    assert client.get("/api/criminals/?max_reward=0").json() == []

def test_filter_hunts(client):
    rows = client.get("/api/hunts/?criminal_id=5").json()
    assert len(rows) == 2
    assert all(h["criminal_id"] == 5 for h in rows)
    assert client.get("/api/hunts/?criminal_id=999999").json() == []

def test_hunt_lifecycle(client):
    payload = dict(criminal_id=3, success=False, notes="Target escaped.")
    response = client.post("/api/hunts/", json=payload)
    assert response.status_code == 201
    hunt = response.json()
    assert hunt["created_at"]
    url = f"/api/hunts/{hunt['id']}/"
    assert client.get(url).json() == hunt
    updated = client.patch(url, json={"success": True})
    assert updated.status_code == 200
    assert updated.json()["success"] is True
    assert updated.json()["notes"] == payload["notes"]
    assert updated.json()["created_at"] == hunt["created_at"]
    assert client.patch(url, json={"notes": "Captured."}).json()["success"] is True
    # false must survive a partial update too.
    assert client.patch(url, json={"success": False}).json()["success"] is False
    deleted = client.delete(url)
    assert deleted.status_code == 204 and deleted.content == b""
    assert client.get(url).status_code == 404
    assert client.patch(url, json={"success": True}).status_code == 404
    assert client.delete(url).status_code == 404

@pytest.mark.parametrize("path,code", [
    ("/api/criminals/999999/",404), ("/api/hunts/999999/",404),
    ("/api/hunts/0/",422), ("/api/criminals/abc/",422),
    ("/api/criminals/?sort=name",422), ("/api/criminals/?armed=maybe",422),
    ("/api/criminals/?min_reward=-1",422),
    ("/api/criminals/?min_reward=100&max_reward=10",422),
    ("/api/hunts/?criminal_id=-1",422),
])
def test_invalid_reads(client, path, code):
    assert client.get(path).status_code == code

@pytest.mark.parametrize("body,code", [
    ({"criminal_id":999999,"success":False,"notes":"x"},404),
    ({"criminal_id":1,"success":False,"notes":"x","created_at":"2020-01-01T00:00:00Z"},422),
    ({"criminal_id":1,"success":"false","notes":"x"},422),
    ({"criminal_id":True,"success":False,"notes":"x"},422),
    ({"criminal_id":1,"success":False},422),
    ({"criminal_id":1,"success":False,"notes":None},422),
])
def test_invalid_create(client, body, code):
    assert client.post("/api/hunts/",json=body).status_code == code

@pytest.mark.parametrize("body", [{}, {"notes":None}, {"success":None},
    {"created_at":"2020-01-01T00:00:00Z"}, {"criminal_id":2}, {"success":"yes"}])
def test_invalid_patch(client, body):
    assert client.patch("/api/hunts/1/",json=body).status_code == 422

def test_openapi(client):
    schema = client.get("/openapi.json")
    assert schema.status_code == 200
    assert "/api/hunts/{id}/" in schema.json()["paths"]

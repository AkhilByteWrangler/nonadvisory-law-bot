import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_ask():
    resp = client.post('/ask', json={"question": "What is minimum wage in NY?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "timestamp" in data

def test_feedback():
    resp = client.post('/feedback', json={"message": "Test message", "emoji": "👍", "timestamp": 1719168000000})
    assert resp.status_code == 200
    assert "reply" in resp.json()

def test_history():
    resp = client.get('/history')
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_clear_history():
    resp = client.delete('/history')
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

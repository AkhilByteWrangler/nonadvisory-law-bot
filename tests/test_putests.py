import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_ask_valid():
    resp = client.post('/ask', json={"question": "What is the minimum wage in California?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "timestamp" in data
    assert isinstance(data["timestamp"], int)

def test_ask_empty():
    resp = client.post('/ask', json={"question": ""})
    assert resp.status_code == 200 or resp.status_code == 422

def test_feedback_valid():
    resp = client.post('/feedback', json={"message": "Test message", "emoji": "👍", "timestamp": 1719168000000})
    assert resp.status_code == 200
    assert "reply" in resp.json()

def test_feedback_invalid():
    resp = client.post('/feedback', json={"message": "", "emoji": "", "timestamp": 0})
    assert resp.status_code == 200 or resp.status_code == 422

def test_history_and_clear():
    resp = client.get('/history')
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    resp = client.delete('/history')
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

def test_get_feedback():
    resp = client.get('/feedback')
    assert resp.status_code == 200
    assert "future_improvement_feedback" in resp.json()

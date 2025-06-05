import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_user_registration_and_login():
    # Register user
    response = client.post("/users/", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 201
    # Login user
    response = client.post("/token", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    return data["access_token"]

def test_protected_endpoint_requires_auth():
    response = client.get("/documents")
    assert response.status_code == 401

def test_protected_endpoint_with_auth():
    token = test_user_registration_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/documents", headers=headers)
    assert response.status_code == 200
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def auth_token():
    client.post("/users/", data={"username": "cruduser", "password": "crudpass"})
    response = client.post("/token", data={"username": "cruduser", "password": "crudpass"})
    return response.json()["access_token"]

def test_create_and_get_document(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Create document
    response = client.post("/documents", data={"name": "Doc1", "content": "Hello world"}, headers=headers)
    assert response.status_code == 200 or response.status_code == 201
    doc_id = response.json()["id"]
    # Get document
    response = client.get(f"/documents/{doc_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Doc1"

def test_update_and_delete_document(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Create document
    response = client.post("/documents", data={"name": "Doc2", "content": "Bye world"}, headers=headers)
    doc_id = response.json()["id"]
    # Update document
    response = client.put(f"/documents/{doc_id}", data={"name": "Doc2-updated"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Doc2-updated"
    # Delete document
    response = client.delete(f"/documents/{doc_id}", headers=headers)
    assert response.status_code == 200
    assert "deleted" in response.json()["detail"]
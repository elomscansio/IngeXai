import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk

client = TestClient(app)

def delete_test_user(username):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            doc_ids = [doc.id for doc in db.query(Document.id).filter(Document.owner_id == user.id)]
            if doc_ids:
                db.query(DocumentChunk).filter(DocumentChunk.document_id.in_(doc_ids)).delete(synchronize_session=False)
                db.query(Document).filter(Document.id.in_(doc_ids)).delete(synchronize_session=False)
            db.delete(user)
            db.commit()
    finally:
        db.close()


def test_user_registration_and_login():
    delete_test_user("testuser")
    # Register user
    response = client.post("/users/", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 201
    data = response.json()
    assert data["status"] is True
    assert data["data"]["username"] == "testuser"
    # Login user
    response = client.post("/users/token", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_protected_endpoint_requires_auth():
    response = client.get("/documents")
    assert response.status_code == 401

@pytest.fixture
def auth_token():
    delete_test_user("testuser")
    client.post("/users/", data={"username": "testuser", "password": "testpass"})
    response = client.post("/users/token", data={"username": "testuser", "password": "testpass"})
    return response.json()["access_token"]

def test_protected_endpoint_with_auth(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/documents", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] is True
    assert isinstance(data["data"], list)
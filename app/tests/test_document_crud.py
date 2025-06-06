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
            # Find all document ids owned by the user
            doc_ids = [doc.id for doc in db.query(Document.id).filter(Document.owner_id == user.id)]
            if doc_ids:
                # Delete all document chunks for these documents
                db.query(DocumentChunk).filter(DocumentChunk.document_id.in_(doc_ids)).delete(synchronize_session=False)
                # Delete all documents owned by the user
                db.query(Document).filter(Document.id.in_(doc_ids)).delete(synchronize_session=False)
            db.delete(user)
            db.commit()
    finally:
        db.close()

@pytest.fixture
def auth_token():
    delete_test_user("cruduser")
    client.post("/users/", data={"username": "cruduser", "password": "crudpass"})
    response = client.post("/users/token", data={"username": "cruduser", "password": "crudpass"})
    return response.json()["data"]["access_token"]

def test_create_and_get_document(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Create document (simulate upload)
    files = {"file": ("Doc1.txt", b"Hello world", "text/plain")}
    response = client.post("/documents/upload", files=files, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] is True
    doc_id = int(data["data"]["document_id"])
    # Get document
    response = client.get(f"/documents/{doc_id}", headers=headers)
    assert response.status_code == 200
    doc_data = response.json()
    assert doc_data["status"] is True
    assert doc_data["data"]["document"]["name"] == "Doc1.txt"

def test_update_and_delete_document(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Create document (simulate upload)
    files = {"file": ("Doc2.txt", b"Bye world", "text/plain")}
    response = client.post("/documents/upload", files=files, headers=headers)
    doc_id = int(response.json()["data"]["document_id"])
    # Update document
    response = client.put(f"/documents/{doc_id}", data={"name": "Doc2-updated"}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] is True
    assert data["data"]["document"]["name"] == "Doc2-updated"
    # Delete document
    response = client.delete(f"/documents/{doc_id}", headers=headers)
    assert response.status_code == 200
    del_data = response.json()
    assert del_data["status"] is True
    assert del_data["data"]["external_status"] == "deleted"
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
import logging

from app.core.auth import authenticate_user, get_password_hash, get_db, get_current_user
from app.models.document import User, Document, DocumentChunk
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.services import mock_external, vector_store

router = APIRouter()

SECRET_KEY = "supersecret"  # Should be from config/env
ALGORITHM = "HS256"

@router.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    docs = db.query(Document).filter(Document.owner_id == current_user.id).all()
    return [
        {"id": d.id, "name": d.name, "created_at": d.created_at}
        for d in docs
    ]

@router.get("/documents/{doc_id}")
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == doc_id, Document.owner_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
    # Returns document metadata and full content
    return {
        "id": doc.id,
        "name": doc.name,
        "created_at": doc.created_at,
        "content": doc.content,
        "chunks": [
            {"chunk_index": c.chunk_index, "chunk_text": c.chunk_text, "status": c.status}
            for c in chunks
        ]
    }

@router.get("/documents/{doc_id}/chunks")
def get_document_chunks(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == doc_id, Document.owner_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
    # Returns all chunks for the document
    return [
        {
            "id": c.id,
            "chunk_index": c.chunk_index,
            "chunk_text": c.chunk_text,
            "status": c.status,
            "created_at": c.created_at,
            "embedding": c.embedding
        }
        for c in chunks
    ]

@router.put("/documents/{doc_id}")
def update_document(
    doc_id: int,
    name: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == doc_id, Document.owner_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if name:
        doc.name = name
    db.commit()
    db.refresh(doc)
    return {"id": doc.id, "name": doc.name}

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logging.info(f"User {current_user.username} uploading file: {file.filename}")
    # Validate file type
    if file.content_type not in [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]:
        logging.warning(f"Unsupported file type: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type"
        )
    file_bytes = await file.read()
    # Extract text
    if file.content_type == "application/pdf":
        text = doc_ingestion.extract_text_from_pdf(file_bytes)
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = doc_ingestion.extract_text_from_docx(file_bytes)
    else:
        text = doc_ingestion.extract_text_from_txt(file_bytes)
    # Store document
    document = Document(
        name=file.filename,
        owner_id=current_user.id,
        content=text
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    # Simulate external document creation
    ext_result = mock_external.external_create_document({"name": file.filename, "owner": current_user.username})
    # Chunk text and store chunks
    chunks = doc_ingestion.chunk_text(text)
    for idx, chunk in enumerate(chunks):
        embedding = vector_store.mock_embedding(chunk)
        doc_chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=idx,
            chunk_text=chunk,
            embedding=str(embedding)
        )
        db.add(doc_chunk)
        db.flush()  # Get chunk id before commit
        vector_store.vector_store.add_vector(doc_chunk.id, embedding)
    db.commit()
    logging.info(f"Document {document.id} uploaded and ingested by user {current_user.username}")
    return {
        "document_id": document.id,
        "chunks": len(chunks),
        "external_status": ext_result["status"],
        "external_id": ext_result["external_id"]
    }

@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logging.info(f"User {current_user.username} deleting document {doc_id}")
    doc = db.query(Document).filter(Document.id == doc_id, Document.owner_id == current_user.id).first()
    if not doc:
        logging.warning(f"Document {doc_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Document not found")
    # Simulate external document deletion
    ext_result = mock_external.external_delete_document(f"ext_{doc.name}")
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
    db.delete(doc)
    db.commit()
    logging.info(f"Document {doc_id} and its chunks deleted by user {current_user.username}")
    return {
        "detail": "Document and its chunks deleted",
        "external_status": ext_result["status"],
        "external_id": ext_result["external_id"]
    }

@router.post("/users/", status_code=201)
def create_user(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    logging.info(f"Attempt to create user: {username}")
    if db.query(User).filter(User.username == username).first():
        logging.warning(f"Username already registered: {username}")
        raise HTTPException(status_code=400, detail="Username already registered")
    user = User(username=username, hashed_password=get_password_hash(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    logging.info(f"User created: {username}")
    return {"id": user.id, "username": user.username}

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logging.info(f"Login attempt for user: {form_data.username}")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logging.warning(f"Failed login for user: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token_data = {"sub": user.username}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    logging.info(f"User logged in: {form_data.username}")
    return {"access_token": token, "token_type": "bearer"}

# Protected endpoints (require authentication)

@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username}

@router.post("/documents/search_chunks")
def search_document_chunks(
    query: str = Form(...),
    top_k: int = Form(5),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search for the most similar document chunks to the query using the in-memory vector store.
    """
    # Generate a mock embedding for the query
    query_embedding = vector_store.mock_embedding(query)
    # Get top_k chunk IDs from the vector store
    chunk_ids = vector_store.vector_store.search(query_embedding, top_k=top_k)
    # Retrieve chunk info from the database
    chunks = db.query(DocumentChunk).filter(DocumentChunk.id.in_(chunk_ids)).all()
    return [
        {
            "id": c.id,
            "document_id": c.document_id,
            "chunk_index": c.chunk_index,
            "chunk_text": c.chunk_text,
            "embedding": c.embedding,
            "status": c.status,
            "created_at": c.created_at
        }
        for c in chunks
    ]

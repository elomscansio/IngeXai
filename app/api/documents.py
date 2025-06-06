from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Form
from jose import jwt
import logging

from app.core.auth import authenticate_user, get_password_hash, get_db, get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.services import mock_external, vector_store
from app.services import doc_ingestion
from app.schemas.documents import (
    DocumentBaseSchema, DocumentChunkSchema, DocumentListResponse, DocumentDetail, DocumentDetailResponse, DocumentChunkListResponse, DocumentUploadResponse, DocumentDeleteResponse, DocumentUploadResponseDetail, DocumentDeleteResponseDetail
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    docs = db.query(Document).filter(Document.owner_id == current_user.id).all()
    data = [DocumentBaseSchema.from_orm(d) for d in docs]
    return DocumentListResponse(
        message="Documents fetched successfully",
        status=True,
        status_code=200,
        data=data
    )

@router.get("/{doc_id}", response_model=DocumentDetailResponse)
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == doc_id, Document.owner_id == current_user.id).first()
    if not doc:
        return DocumentDetailResponse(
            message="Document not found",
            status=False,
            status_code=404,
            data=None
        )
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
    chunk_data = [DocumentChunkSchema.from_orm(c) for c in chunks]
    data = DocumentDetail(
        document=DocumentBaseSchema.from_orm(doc),
        chunks=chunk_data
    )
    return DocumentDetailResponse(
        message="Document fetched successfully",
        status=True,
        status_code=200,
        data=data
    )

@router.get("/{doc_id}/chunks", response_model=DocumentChunkListResponse)
def get_document_chunks(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == doc_id, Document.owner_id == current_user.id).first()
    if not doc:
        return DocumentChunkListResponse(
            message="Document not found",
            status=False,
            status_code=404,
            data=None
        )
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
    data = [DocumentChunkSchema.from_orm(c) for c in chunks]
    return DocumentChunkListResponse(
        message="Document chunks fetched successfully",
        status=True,
        status_code=200,
        data=data
    )

@router.put("/{doc_id}", response_model=DocumentDetailResponse)
def update_document(
    doc_id: int,
    name: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == doc_id, Document.owner_id == current_user.id).first()
    if not doc:
        return DocumentDetailResponse(
            message="Document not found",
            status=False,
            status_code=404,
            data=None
        )
    if name:
        doc.name = name
    db.commit()
    db.refresh(doc)
    data = DocumentDetail(
        document=DocumentBaseSchema.from_orm(doc),
        chunks=[]
    )
    return DocumentDetailResponse(
        message="Document updated successfully",
        status=True,
        status_code=200,
        data=data
    )

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logging.info(f"User {current_user.username} uploading file: {file.filename}")
    if file.content_type not in [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]:
        logging.warning(f"Unsupported file type: {file.content_type}")
        return DocumentUploadResponse(
            message="Unsupported file type",
            status=False,
            status_code=400,
            data=None
        )
    file_bytes = await file.read()
    if file.content_type == "application/pdf":
        text = doc_ingestion.extract_text_from_pdf(file_bytes)
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = doc_ingestion.extract_text_from_docx(file_bytes)
    else:
        text = doc_ingestion.extract_text_from_txt(file_bytes)
    document = Document(
        name=file.filename,
        owner_id=current_user.id,
        content=text
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    ext_result = mock_external.external_create_document({"name": file.filename, "owner": current_user.username})
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
        db.flush()
        vector_store.vector_store.add_vector(doc_chunk.id, embedding)
    db.commit()
    return DocumentUploadResponse(
        message="Document uploaded and ingested successfully",
        status=True,
        status_code=201,
        data=DocumentUploadResponseDetail(
            document_id=str(document.id),
            chunks=len(chunks),
            external_status=ext_result["status"],
            external_id=ext_result["external_id"]
        )
    )

@router.delete("/{doc_id}", response_model=DocumentDeleteResponse)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logging.info(f"User {current_user.username} deleting document {doc_id}")
    doc = db.query(Document).filter(Document.id == doc_id, Document.owner_id == current_user.id).first()
    if not doc:
        return DocumentDeleteResponse(
            message="Document not found",
            status=False,
            status_code=404,
            data=None
        )
    ext_result = mock_external.external_delete_document(f"ext_{doc.name}")
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
    db.delete(doc)
    db.commit()
    return DocumentDeleteResponse(
        message="Document and its chunks deleted",
        status=True,
        status_code=200,
        data=DocumentDeleteResponseDetail(
            external_status=ext_result["status"],
            external_id=ext_result["external_id"]
        )
    )

@router.post("/search_chunks", response_model=DocumentChunkListResponse)
def search_document_chunks(
    query: str = Form(...),
    top_k: int = Form(5),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query_embedding = vector_store.mock_embedding(query)
    chunk_ids = vector_store.vector_store.search(query_embedding, top_k=top_k)
    chunks = db.query(DocumentChunk).filter(DocumentChunk.id.in_(chunk_ids)).all()
    data = [DocumentChunkSchema.from_orm(c) for c in chunks]
    return DocumentChunkListResponse(
        message="Search successful",
        status=True,
        status_code=200,
        data=data  # If the response model expects a list, keep this. If it expects a DocumentDetail, wrap accordingly.
    )

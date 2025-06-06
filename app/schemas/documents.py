from typing import Any, Optional
from pydantic import BaseModel
from app.schemas.base import BaseResponseSchema


class DocumentBaseSchema(BaseModel):
    id: int
    name: str
    created_at: Any
    updated_at: Any
    content: Optional[str] = None
    model_config = {'from_attributes': True}


class DocumentChunkSchema(BaseModel):
    id: int
    document_id: Optional[int] = None
    chunk_index: int
    chunk_text: str
    embedding: Optional[str] = None
    status: Optional[str] = None
    created_at: Any
    updated_at: Any
    model_config = {'from_attributes': True}


class DocumentListResponse(BaseResponseSchema):
    data: Optional[list[DocumentBaseSchema]]


class DocumentDetail(BaseModel):
    document: DocumentBaseSchema
    chunks: list[DocumentChunkSchema]


class DocumentDetailResponse(BaseResponseSchema):
    data: Optional[DocumentDetail]


class DocumentChunkListResponse(DocumentDetailResponse):
    # already inherits from DocumentDetailResponse
    pass


class DocumentUploadResponseDetail(BaseModel):
    document_id: str
    chunks: int
    external_status: Any
    external_id: Any


class DocumentUploadResponse(BaseResponseSchema):
    data: Optional[DocumentUploadResponseDetail]


class DocumentDeleteResponseDetail(BaseModel):
    external_status: Any
    external_id: Any


class DocumentDeleteResponse(BaseResponseSchema):
    data: Optional[DocumentDeleteResponseDetail]

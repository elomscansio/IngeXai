from sqlalchemy import Column, String, Text, Integer, ForeignKey
from app.models.base import BaseModel


class DocumentChunk(BaseModel):
    __tablename__ = "document_chunks"
    document_id = Column(
        Integer, ForeignKey("documents.id"), nullable=False, index=True
    )
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)
    status = Column(String, default="active")

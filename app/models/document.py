from sqlalchemy import Column, String, Text, Integer, ForeignKey
from app.models.base import BaseModel


class Document(BaseModel):
    __tablename__ = "documents"
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)

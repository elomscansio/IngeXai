from sqlalchemy import Column, String, Boolean
from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"
    username = Column(String, unique=True, nullable=False, index=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    hashed_password = Column(String, nullable=False)

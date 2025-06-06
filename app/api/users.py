from fastapi import APIRouter, HTTPException, status, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app.services.user import authenticate_user, get_password_hash
from app.core.auth import get_db, get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from sqlalchemy.orm import Session
from app.schemas.base import BaseResponseSchema
from app.schemas.users import (
    UserBaseSchema,
    UserLoginResponse,
    UserListResponse,
    UserDetailResponse,
    UserCreateResponse,
    UserDeleteResponse,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", status_code=201, response_model=UserCreateResponse)
def create_user(
    username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)
):
    logging.info(f"Attempt to create user: {username}")
    if db.query(User).filter(User.username == username).first():
        logging.warning(f"Username already registered: {username}")
        return UserCreateResponse(
            message="Username already registered",
            status=False,
            status_code=400,
            data=None,
        )
    user = User(username=username, hashed_password=get_password_hash(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    logging.info(f"User created: {username}")
    return UserCreateResponse(
        message="User created successfully",
        status=True,
        status_code=201,
        data=UserBaseSchema.from_orm(user),
    )


@router.post("/token", response_model=UserLoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    logging.info(f"Login attempt for user: {form_data.username}")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token_data = {"sub": user.username}
    # SECRET_KEY and ALGORITHM should be imported from config or settings
    from app.core.config import SECRET_KEY, ALGORITHM

    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    logging.info(f"User logged in: {form_data.username}")
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserDetailResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return UserDetailResponse(
        message="Current user fetched successfully",
        status=True,
        status_code=200,
        data=UserBaseSchema.from_orm(current_user),
    )


@router.get("/", response_model=UserListResponse)
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    data = [UserBaseSchema.from_orm(u) for u in users]
    return UserListResponse(
        message="Users fetched successfully", status=True, status_code=200, data=data
    )


@router.get("/{user_id}", response_model=UserDetailResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return UserDetailResponse(
            message="User not found", status=False, status_code=404, data=None
        )
    return UserDetailResponse(
        message="User fetched successfully",
        status=True,
        status_code=200,
        data=UserBaseSchema.from_orm(user),
    )


@router.put("/{user_id}", response_model=UserDetailResponse)
def update_user(
    user_id: int,
    username: str = Form(None),
    password: str = Form(None),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return UserDetailResponse(
            message="User not found", status=False, status_code=404, data=None
        )
    if username:
        user.username = username  # type: ignore
    if password:
        user.hashed_password = get_password_hash(password)  # type: ignore
    db.commit()
    db.refresh(user)
    return UserDetailResponse(
        message="User updated successfully",
        status=True,
        status_code=200,
        data=UserBaseSchema.from_orm(user),
    )


@router.delete("/{user_id}", response_model=UserDeleteResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return UserDeleteResponse(
            message="User not found", status=False, status_code=404, data=None
        )
    db.delete(user)
    db.commit()
    return UserDeleteResponse(
        message="User deleted successfully",
        status=True,
        status_code=200,
        data={"id": user_id},
    )

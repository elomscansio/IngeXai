from typing import Any, Optional
from pydantic import BaseModel
from app.schemas.base import BaseResponseSchema


class UserBaseSchema(BaseModel):
    id: int
    username: str
    is_admin: bool
    model_config = {"from_attributes": True}


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str


class UserListResponse(BaseResponseSchema):
    data: Optional[list[UserBaseSchema]]


class UserDetailResponse(BaseResponseSchema):
    data: Optional[UserBaseSchema]


class UserCreateResponse(BaseResponseSchema):
    data: Optional[UserBaseSchema]


class UserDeleteResponse(BaseResponseSchema):
    data: Any

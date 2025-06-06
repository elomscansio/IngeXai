from typing import Any, Optional
from pydantic import BaseModel


class BaseResponseSchema(BaseModel):
    model_config = {'from_attributes': True}

    message: str
    status: bool
    status_code: int
    data: Optional[Any]

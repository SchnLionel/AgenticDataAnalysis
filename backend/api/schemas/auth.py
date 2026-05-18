from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

    model_config = {"from_attributes": True}

class UserCreate(UserBase):
    password: str

    model_config = {"from_attributes": True}

class User(UserBase):
    id: int
    
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str

    model_config = {"from_attributes": True}

class TokenPayload(BaseModel):
    sub: Optional[int] = None

    model_config = {"from_attributes": True}

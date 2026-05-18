from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

    class Config:
        from_attributes = True

class UserCreate(UserBase):
    password: str

    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

    class Config:
        from_attributes = True

class TokenPayload(BaseModel):
    sub: Optional[int] = None

    class Config:
        from_attributes = True

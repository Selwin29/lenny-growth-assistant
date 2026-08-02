from pydantic import BaseModel, EmailStr
from typing import Optional
from app.schemas.user import UserRead

class LoginRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead

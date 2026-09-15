from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from app.models.user import UserRole
from app.schemas.base import DadosEntrada


class UserBase(DadosEntrada):
    username: str = Field(..., min_length=3, max_length=100)
    email: Optional[str] = None
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.AGENTE
    municipio: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    supervisor_id: Optional[int] = None


class UserUpdate(DadosEntrada):
    email: Optional[str] = None
    full_name: Optional[str] = None
    municipio: Optional[str] = None
    is_active: Optional[bool] = None
    supervisor_id: Optional[int] = None
    password: Optional[str] = Field(None, min_length=6)


class UserResponse(UserBase):
    id: int
    is_active: bool
    supervisor_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime



class Token(DadosEntrada):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class LoginRequest(DadosEntrada):
    username: str
    password: str


class ChangePasswordRequest(DadosEntrada):
    current_password: str
    new_password: str = Field(..., min_length=6)


class TokenRefresh(DadosEntrada):
    refresh_token: str

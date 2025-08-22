# src/auth/models.py
# --- agent_meta ---
# role: auth-models
# owner: @backend
# contract: Pydantic-схемы запросов/ответов для /auth/* и /orgs
# last_reviewed: 2025-08-21
# interfaces:
#   - SignupRequest(email: str, password: str, org_name?: str)
#   - LoginRequest(email: str, password: str)
#   - UserOut(id: str, email: str)
#   - MeOut(user: UserOut, org_id: str, role: str)
# --- /agent_meta ---

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    org_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr


class MeOut(BaseModel):
    user: UserOut
    org_id: str
    role: str


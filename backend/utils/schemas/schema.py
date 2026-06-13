from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl


# ===== AUTH SCHEMAS =====
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserCreateResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None


# ===== SERVICE SCHEMAS =====
class ServiceBase(BaseModel):
    name: str
    url: HttpUrl  # Pydantic sam sprawdzi, czy to poprawny link HTTP/HTTPS
    check_interval: int = 60  # Domyślnie sprawdzamy co 60 sekund
    is_active: bool = True

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: str | None = None
    url: HttpUrl | None = None
    check_interval: int | None = None
    is_active: bool | None = None

class ServiceResponse(ServiceBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# ===== CHECKS SCHEMAS =====
class CheckResponse(BaseModel):
    id: int
    status_code: int
    response_time_ms: int
    created_at: datetime
    user_id: int
    service_id: int

    class Config:
        from_attributes = True

# ===== INCIDENTS SCHEMAS =====
class IncidentResponse(BaseModel):
    id: int
    started_at: datetime
    ended_at: Optional[datetime]
    error_message: str
    user_id: int
    service_id: int

    class Config:
        from_attributes = True
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl

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
    url: HttpUrl
    interval: int = Field(60, description="Interval in seconds") # Zgodnie z kolumną w bazie

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    interval: Optional[int] = None

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
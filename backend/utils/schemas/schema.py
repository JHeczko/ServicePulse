from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


# ===== AUTH SCHEMAS =====
class UserCreate(BaseModel):
    # Dozwolone tylko litery, cyfry, podkreślenia i myślniki, brak spacji
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Username can only contain alphanumeric characters, underscores, and dashes."
    )
    # Maksymalna długość chroni przed Password DoS attack (obciążenie algorytmu haszującego)
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="Password must be between 6 and 128 characters long."
    )


class UserCreateResponse(BaseModel):
    id: int
    username: str

    # Nowy standard w Pydantic v2 (zamiast starej klasy Config)
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# ===== SERVICE SCHEMAS =====
class ServiceBase(BaseModel):
    # strip_whitespace=True automatycznie usunie zbędne spacje z początku i końca
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        strip_whitespace=True,
        description="The display name of the monitored service."
    )
    url: HttpUrl
    # ge=10 chroni przed ujemnymi interwałami oraz zajechaniem procesora (min. 10 sekund)
    interval: int = Field(
        60,
        ge=10,
        le=86400,
        description="Interval in seconds (minimum 10s, maximum 1 day)."
    )


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    # Wszystko jest opcjonalne, ale JEŚLI zostanie podane, musi spełniać kryteria
    name: Optional[str] = Field(None, min_length=1, max_length=100, strip_whitespace=True)
    url: Optional[HttpUrl] = None
    interval: Optional[int] = Field(None, ge=10, le=86400)


class ServiceResponse(ServiceBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


# ===== CHECKS SCHEMAS =====
class CheckResponse(BaseModel):
    id: int
    status_code: int = Field(..., ge=0, le=599)
    response_time_ms: int = Field(..., ge=0)
    created_at: datetime
    user_id: int
    service_id: int

    model_config = ConfigDict(from_attributes=True)


# ===== INCIDENTS SCHEMAS =====
class IncidentResponse(BaseModel):
    id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    error_message: str = Field(..., max_length=1000)
    user_id: int
    service_id: int

    model_config = ConfigDict(from_attributes=True)
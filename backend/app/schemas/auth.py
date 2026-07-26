from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .trip import TravelerRead


def _check_password_bytes(value: str) -> str:
    # bcrypt solo procesa 72 bytes; más allá se ignoraría en silencio
    if len(value.encode()) > 72:
        raise ValueError("La contraseña no puede superar 72 bytes")
    return value


class AuthStatus(BaseModel):
    bootstrapped: bool


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)


class BootstrapRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    traveler_name: str = Field(min_length=1, max_length=100)

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return _check_password_bytes(v)

    @field_validator("username", "traveler_name")
    @classmethod
    def strip_names(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("No puede estar vacío")
        return v


class FamilyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class SessionUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    is_admin: bool
    theme: Literal["light", "dark", "system"]
    language: Literal["es", "en"]


class MeRead(BaseModel):
    user: SessionUserRead
    traveler: TravelerRead
    family: FamilyRead | None


class UserSettingsUpdate(BaseModel):
    theme: Literal["light", "dark", "system"] | None = None
    language: Literal["es", "en"] | None = None


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return _check_password_bytes(v)

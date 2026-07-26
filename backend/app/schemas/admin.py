from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .auth import _check_password_bytes
from .trip import TravelerRead


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    is_admin: bool = False
    # vincular un viajero virtual existente O crear uno nuevo (exactamente uno)
    traveler_id: int | None = None
    traveler_name: str | None = Field(default=None, min_length=1, max_length=100)
    family_id: int | None = None

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return _check_password_bytes(v)

    @field_validator("username")
    @classmethod
    def strip_username(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("No puede estar vacío")
        return v

    @model_validator(mode="after")
    def check_traveler(self) -> "UserCreate":
        if (self.traveler_id is None) == (self.traveler_name is None):
            raise ValueError("Indica traveler_id O traveler_name (exactamente uno)")
        return self


class UserUpdate(BaseModel):
    is_admin: bool | None = None


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return _check_password_bytes(v)


class UserAdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    is_admin: bool
    traveler: TravelerRead


class FamilyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class FamilyUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class FamilyReorder(BaseModel):
    ids: list[int]

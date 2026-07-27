from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ChecklistItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    done: bool = False
    due_date: date | None = None
    url: str | None = None
    notes: str | None = None


class ChecklistItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    done: bool | None = None
    due_date: date | None = None
    url: str | None = None
    notes: str | None = None


class ChecklistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    title: str
    done: bool
    due_date: date | None
    url: str | None
    notes: str | None

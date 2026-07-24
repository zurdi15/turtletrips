from pydantic import BaseModel


class RestoreResult(BaseModel):
    restored: bool
    trips: int
    previous_revision: str | None

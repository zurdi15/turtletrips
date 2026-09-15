from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize_url(value: str) -> str:
    """Recorta y antepone https:// si pegan la URL sin esquema ("booking.com/…")."""
    value = value.strip()
    if not value:
        raise ValueError("El enlace no puede estar vacío")
    if not value.lower().startswith(("http://", "https://")):
        value = f"https://{value}"
    return value


# ---- bloques ----


# nombre de icono mdi sin prefijo ("bed", "passport"); la lista la ofrece el front
ICON_PATTERN = r"^[a-z0-9-]{1,40}$"


class LinkGroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    icon: str | None = Field(default=None, pattern=ICON_PATTERN)


class LinkGroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    icon: str | None = Field(default=None, pattern=ICON_PATTERN)


class LinkGroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    name: str
    icon: str | None
    position: int


class LinkGroupReorder(BaseModel):
    """ids de bloque en el orden deseado (la posición es el índice)."""

    ids: list[int]


# ---- enlaces ----


class TripLinkCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=1, max_length=2000)
    notes: str | None = None
    group_id: int | None = None

    _normalize_url = field_validator("url")(_normalize_url)


class TripLinkUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    url: str | None = Field(default=None, min_length=1, max_length=2000)
    notes: str | None = None
    group_id: int | None = None

    _normalize_url = field_validator("url")(_normalize_url)


class TripLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    group_id: int | None
    title: str
    url: str
    notes: str | None
    position: int
    image_url: str | None


class TripLinkBucket(BaseModel):
    """Un bloque (o None = sin bloque) con sus enlaces en orden."""

    group_id: int | None = None
    ids: list[int]


class TripLinkReorder(BaseModel):
    """Disposición completa tras un drag & drop: cada enlace listado toma el
    bloque y la posición del cubo en el que aparece."""

    buckets: list[TripLinkBucket]

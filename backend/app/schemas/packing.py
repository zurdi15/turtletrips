from pydantic import BaseModel, ConfigDict, Field


class PackingItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(default="Ropa", min_length=1, max_length=50)
    url: str | None = None
    checked: bool = False
    traveler_id: int | None = None  # NULL = maleta común


class PackingItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    url: str | None = None
    checked: bool | None = None
    traveler_id: int | None = None


class PackingItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    traveler_id: int | None
    name: str
    category: str
    url: str | None
    checked: bool


class PackingSelectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    traveler_id: int | None
    template_id: int


class PackingTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    from_trip_id: int | None = None
    traveler_id: int | None = None  # maleta de ese viajero (o común) al copiar desde un viaje


class PackingTemplateUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class PackingTemplateRead(BaseModel):
    id: int
    name: str
    item_count: int


class PackingTemplateItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(default="Ropa", min_length=1, max_length=50)
    url: str | None = None


class PackingTemplateItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    url: str | None = None


class PackingTemplateItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int
    name: str
    category: str
    url: str | None


class PackingTemplateDetail(BaseModel):
    id: int
    name: str
    items: list[PackingTemplateItemRead]


class CategoryCreate(BaseModel):
    kind: str = Field(pattern="^(expense|packing)$")
    name: str = Field(min_length=1, max_length=50)
    color: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    color: str | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    name: str
    color: str | None
    position: int

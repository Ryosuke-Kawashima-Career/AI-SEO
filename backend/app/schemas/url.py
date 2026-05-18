from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class UrlCreate(BaseModel):
    url: HttpUrl
    label: str | None = None


class UrlResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    label: str | None
    created_at: datetime

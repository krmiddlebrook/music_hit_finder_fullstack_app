from datetime import date
from typing import Optional, List, Any, Dict

from pydantic import BaseModel

from .label import Label

# from app.schemas.track import Track


# Shared properties
class AlbumBase(BaseModel):
    id: str
    name: Optional[str] = None
    release_date: date
    total_tracks: Optional[int] = None
    type: Optional[str] = None
    label_id: Optional[str] = None
    # label: Optional[Label] = None
    cover: Optional[str] = None


# Properties to receive via API on creation
class AlbumCreate(AlbumBase):
    # TODO: add artist_ids list
    pass


# Properties to receive via API on update
class AlbumUpdate(AlbumBase):
    pass


# Properties shared by models stored in DB
class AlbumInDBBase(AlbumBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class Album(AlbumInDBBase):
    pass


# Additional properties stored in DB
class AlbumInDB(AlbumInDBBase):
    pass

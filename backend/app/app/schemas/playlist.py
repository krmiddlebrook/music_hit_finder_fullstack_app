from typing import Optional

from pydantic import BaseModel


# Shared properties
class PlaylistBase(BaseModel):
    id: str
    owner_id: str
    name: Optional[str] = None


# Properties to receive via API on creation
class PlaylistCreate(PlaylistBase):
    pass


# Properties to receive via API on update
class PlaylistUpdate(PlaylistBase):
    name: str


# Properties shared by models stored in DB
class PlaylistInDBBase(PlaylistBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class Playlist(PlaylistInDBBase):
    pass


# Additional properties stored in DB
class PlaylistInDB(PlaylistInDBBase):
    pass

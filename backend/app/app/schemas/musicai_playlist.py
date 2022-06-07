from typing import Optional
import datetime

from pydantic import BaseModel


# Shared properties
class MusicaiPlaylistBase(BaseModel):
    playlist_id: str
    owner_id: str
    playlist_url: Optional[str] = None
    last_updated: Optional[datetime.date] = None


# Properties to receive via API on creation
class MusicaiPlaylistCreate(MusicaiPlaylistBase):
    # last_updated: datetime.date
    pass


# Properties to receive via API on update
class MusicaiPlaylistUpdate(MusicaiPlaylistBase):
    # last_updated: datetime.date
    pass


# Properties shared by models stored in DB
class MusicaiPlaylistInDBBase(MusicaiPlaylistBase):
    last_updated: datetime.date

    class Config:
        orm_mode = True


# Additional properties to return via API
class MusicaiPlaylist(MusicaiPlaylistInDBBase):
    last_updated: datetime.date


# Additional properties stored in DB
class MusicaiPlaylistInDB(MusicaiPlaylistInDBBase):
    pass

from pydantic import BaseModel


# Shared properties
class TrackPlaylistBase(BaseModel):
    track_id: str
    playlist_id: str


# Properties to receive via API on creation
class TrackPlaylistCreate(TrackPlaylistBase):
    pass


# Properties to receive via API on update
class TrackPlaylistUpdate(TrackPlaylistBase):
    pass


# Properties shared by models stored in DB
class TrackPlaylistInDBBase(TrackPlaylistBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class TrackPlaylist(TrackPlaylistInDBBase):
    pass


# Additional properties stored in DB
class TrackPlaylistInDB(TrackPlaylistInDBBase):
    pass

from pydantic import BaseModel


# Shared properties
class TermPlaylistBase(BaseModel):
    term_id: str
    playlist_id: str


# Properties to receive via API on creation
class TermPlaylistCreate(TermPlaylistBase):
    pass


# Properties to receive via API on update
class TermPlaylistUpdate(TermPlaylistBase):
    pass


# Properties shared by models stored in DB
class TermPlaylistInDBBase(TermPlaylistBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class TermPlaylist(TermPlaylistInDBBase):
    pass


# Additional properties stored in DB
class TermPlaylistInDB(TermPlaylistInDBBase):
    pass

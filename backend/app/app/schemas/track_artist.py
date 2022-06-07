from pydantic import BaseModel


# Shared properties
class TrackArtistBase(BaseModel):
    track_id: str
    artist_id: str


# Properties to receive via API on creation
class TrackArtistCreate(TrackArtistBase):
    pass


# Properties to receive via API on update
class TrackArtistUpdate(TrackArtistBase):
    pass


# Properties shared by models stored in DB
class TrackArtistInDBBase(TrackArtistBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class TrackArtist(TrackArtistInDBBase):
    pass


# Additional properties stored in DB
class TrackArtistInDB(TrackArtistInDBBase):
    pass

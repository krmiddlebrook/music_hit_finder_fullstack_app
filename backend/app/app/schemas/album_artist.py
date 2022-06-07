from pydantic import BaseModel


# Shared properties
class AlbumArtistBase(BaseModel):
    album_id: str
    artist_id: str


# Properties to receive via API on creation
class AlbumArtistCreate(AlbumArtistBase):
    pass


# Properties to receive via API on update
class AlbumArtistUpdate(AlbumArtistBase):
    pass


# Properties shared by models stored in DB
class AlbumArtistInDBBase(AlbumArtistBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class AlbumArtist(AlbumArtistInDBBase):
    pass


# Additional properties stored in DB
class AlbumArtistInDB(AlbumArtistInDBBase):
    pass

from pydantic import BaseModel


# Shared properties
class GenreArtistBase(BaseModel):
    genre_id: str
    artist_id: str


# Properties to receive via API on creation
class GenreArtistCreate(GenreArtistBase):
    pass


# Properties to receive via API on update
class GenreArtistUpdate(GenreArtistBase):
    pass


# Properties shared by models stored in DB
class GenreArtistInDBBase(GenreArtistBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class GenreArtist(GenreArtistInDBBase):
    pass


# Additional properties stored in DB
class GenreArtistInDB(GenreArtistInDBBase):
    pass

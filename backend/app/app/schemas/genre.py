from pydantic import BaseModel


# Shared properties
class GenreBase(BaseModel):
    id: str


# Properties to receive via API on creation
class GenreCreate(GenreBase):
    pass


# Properties to receive via API on update
class GenreUpdate(GenreBase):
    pass


# Properties shared by models stored in DB
class GenreInDBBase(GenreBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class Genre(GenreInDBBase):
    pass


# Additional properties stored in DB
class GenreInDB(GenreInDBBase):
    pass

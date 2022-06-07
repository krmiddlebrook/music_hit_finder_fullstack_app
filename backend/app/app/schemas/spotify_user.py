from typing import Optional

from pydantic import BaseModel


# Shared properties
class SpotifyUserBase(BaseModel):
    id: str
    name: Optional[str] = None


# Properties to receive via API on creation
class SpotifyUserCreate(SpotifyUserBase):
    pass


# Properties to receive via API on update
class SpotifyUserUpdate(SpotifyUserBase):
    name: Optional[str] = None


# Properties shared by models stored in DB
class SpotifyUserInDBBase(SpotifyUserBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class SpotifyUser(SpotifyUserInDBBase):
    pass


# Additional properties stored in DB
class SpotifyUserInDB(SpotifyUserInDBBase):
    pass

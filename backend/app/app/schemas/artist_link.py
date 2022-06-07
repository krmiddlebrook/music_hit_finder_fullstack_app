from typing import Optional
from datetime import date

from pydantic import BaseModel


# Shared properties
class ArtistLinkBase(BaseModel):
    link: str
    artist_id: str
    link_type: str
    date_added: Optional[date] = date.today()


# Properties to receive via API on creation
class ArtistLinkCreate(ArtistLinkBase):
    pass


# Properties to receive via API on update
class ArtistLinkUpdate(ArtistLinkBase):
    pass


# Properties shared by models stored in DB
class ArtistLinkInDBBase(ArtistLinkBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class ArtistLink(ArtistLinkInDBBase):
    pass


# Additional properties stored in DB
class ArtistLinkInDB(ArtistLinkInDBBase):
    pass


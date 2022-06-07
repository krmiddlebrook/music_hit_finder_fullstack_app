from datetime import date
from typing import Optional
from pydantic import BaseModel


# Shared properties
class TrackPlaycountBase(BaseModel):
    id: str
    track_id: str
    date: date
    playcount: int
    popularity: Optional[int] = None


# Properties to receive via API on creation
class TrackPlaycountCreate(TrackPlaycountBase):
    pass


# Properties to receive via API on update
class TrackPlaycountUpdate(TrackPlaycountBase):
    pass


# Properties shared by models stored in DB
class TrackPlaycountInDBBase(TrackPlaycountBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class TrackPlaycount(TrackPlaycountInDBBase):
    pass


# Additional properties stored in DB
class TrackPlaycountInDB(TrackPlaycountInDBBase):
    pass

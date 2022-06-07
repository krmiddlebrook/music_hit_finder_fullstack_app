from typing import Optional

from pydantic import BaseModel


# Shared properties
class TrackUserBase(BaseModel):
    track_id: str
    user_id: str
    top_track: Optional[bool] = False
    source: Optional[str] = None


# Properties to receive via API on creation
class TrackUserCreate(TrackUserBase):
    pass


# Properties to receive via API on update
class TrackUserUpdate(TrackUserBase):
    pass


# Properties shared by models stored in DB
class TrackUserInDBBase(TrackUserBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class TrackUser(TrackUserInDBBase):
    pass


# Additional properties stored in DB
class TrackUserInDB(TrackUserInDBBase):
    pass

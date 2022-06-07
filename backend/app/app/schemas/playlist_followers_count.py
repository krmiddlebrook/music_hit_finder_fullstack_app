from datetime import date
from pydantic import BaseModel


# Shared properties
class PlaylistFollowersCountBase(BaseModel):
    id: str
    playlist_id: str
    date: date
    followers_count: int


# Properties to receive via API on creation
class PlaylistFollowersCountCreate(PlaylistFollowersCountBase):
    pass


# Properties to receive via API on update
class PlaylistFollowersCountUpdate(PlaylistFollowersCountBase):
    pass


# Properties shared by models stored in DB
class PlaylistFollowersCountInDBBase(PlaylistFollowersCountBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class PlaylistFollowersCount(PlaylistFollowersCountInDBBase):
    pass


# Additional properties stored in DB
class PlaylistFollowersCountInDB(PlaylistFollowersCountInDBBase):
    pass

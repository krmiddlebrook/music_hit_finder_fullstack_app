# from typing import Optional
from datetime import date
from pydantic import BaseModel


# Shared properties
class UserFollowersCountBase(BaseModel):
    id: str
    user_id: str
    date: date
    followers_count: int


# Properties to receive via API on creation
class UserFollowersCountCreate(UserFollowersCountBase):
    pass


# Properties to receive via API on update
class UserFollowersCountUpdate(UserFollowersCountBase):
    followers_count: int


# Properties shared by models stored in DB
class UserFollowersCountInDBBase(UserFollowersCountBase):
    pass

    class Config:
        orm_mode = True


# Additional properties to return via API
class UserFollowersCount(UserFollowersCountInDBBase):
    pass


# Additional properties stored in DB
class UserFollowersCountInDB(UserFollowersCountInDBBase):
    pass

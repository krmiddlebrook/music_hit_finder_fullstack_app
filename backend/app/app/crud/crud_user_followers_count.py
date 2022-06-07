from app.crud.base import CRUDBase
from app.models.user_followers_count import User_Followers_Count
from app.schemas.user_followers_count import (
    UserFollowersCountCreate,
    UserFollowersCountUpdate,
)


class CRUDUserFollowersCount(
    CRUDBase[User_Followers_Count, UserFollowersCountCreate, UserFollowersCountUpdate]
):
    pass


user_followers_count = CRUDUserFollowersCount(User_Followers_Count)

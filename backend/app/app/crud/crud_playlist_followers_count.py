from app.crud.base import CRUDBase
from app.models.playlist_followers_count import Playlist_Followers_Count
from app.schemas.playlist_followers_count import (
    PlaylistFollowersCountCreate,
    PlaylistFollowersCountUpdate,
)


class CRUDPlaylistFollowersCount(
    CRUDBase[
        Playlist_Followers_Count,
        PlaylistFollowersCountCreate,
        PlaylistFollowersCountUpdate,
    ]
):
    pass


playlist_followers_count = CRUDPlaylistFollowersCount(Playlist_Followers_Count)

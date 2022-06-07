from datetime import date

from typing import Dict, Optional, Any

from app.spotify.parser.base import ParseBase
from app.schemas import PlaylistFollowersCount, PlaylistFollowersCountCreate


class ParsePlaylistFollowersCount(
    ParseBase[PlaylistFollowersCount, PlaylistFollowersCountCreate]
):
    def from_playlist(
        self, *, obj_in: Dict[str, Any]
    ) -> Optional[PlaylistFollowersCount]:
        """
        Parse playlist from a search term playlist result or a
        spotify user profile view playlist result.
        
        Ex 1 - search term playlist: {
            author: "Soy William"
            followersCount: 32608
            image: "https://o.scdn.co/300/ab67616d00001e02c450c89d3eb7..."
            name: "HIP HOP 2020 🔥 New Rap & Trap Hits"
            uri: "spotify:user:williamdzn:playlist:0FAb3s3yJArWnikZbEOO9p"
        }
        Ex 2 - user profile view playlist {
            followers_count: 1
            image_url: "spotify:mosaic:ab67616d00001e02118e97a0b3d220210c482b6c:..."
            is_following: true
            name: "Camp 🔥"
            uri: "spotify:user:krmiddlebrook:playlist:02PjZzjbYAzyUhr0uQyVXo"
        }
        """
        if not obj_in.get("uri", None):
            return None

        if (
            obj_in.get("followersCount", None) is None
            and obj_in.get("followers_count", None) is None
        ):
            return None

        uri = obj_in["uri"].split(":")
        if len(uri) != 5:
            return None

        today = date.today()
        f_cnt_id = f'{uri[-1]}_{today.strftime("%Y-%m-%d")}'

        if obj_in.get("followersCount", None):
            obj_in["followers_count"] = obj_in["followersCount"]

        return PlaylistFollowersCount(
            id=f_cnt_id,
            playlist_id=uri[-1],
            date=today,
            followers_count=obj_in["followers_count"],
        )


playlist_followers_count = ParsePlaylistFollowersCount(PlaylistFollowersCount)

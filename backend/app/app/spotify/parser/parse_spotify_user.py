from typing import Dict, Optional, Any

from app.spotify.parser.base import ParseBase
from app.schemas import SpotifyUser, SpotifyUserCreate


class ParseSpotifyUser(ParseBase[SpotifyUser, SpotifyUserCreate]):
    def from_search_term_playlist(
        self, *, obj_in: Dict[str, Any]
    ) -> Optional[SpotifyUser]:
        """
        Parse spotify user from a search term playlist
        Ex Input: {
            author: "Soy William"
            followersCount: 32608
            image: "https://o.scdn.co/300/ab67616d00001e02c450c89d3eb750d3535b0a0cab67616d00001e02d46a8fffbe6c8630784f04daab67616d00001e02e818d05b79be19f4d49f1ebfab67616d00001e02ff8c985ecb3b7c5f847be357"
            name: "HIP HOP 2020 🔥 New Rap & Trap Hits"
            uri: "spotify:user:williamdzn:playlist:0FAb3s3yJArWnikZbEOO9p"
        }
        """
        if "uri" not in obj_in:
            return None

        uri = obj_in["uri"].split(":")
        if len(uri) != 5:
            return None

        return SpotifyUser(id=uri[2], name=obj_in.get("author", None))

    def from_playlist_track(
        self, *, obj_in: Dict[str, Any], owner_name: Optional[str] = None
    ) -> Optional[SpotifyUser]:
        if "added_by" in obj_in:
            obj_in = obj_in["added_by"]

        if "id" not in obj_in:
            return None

        if obj_in["id"] == "":
            # Playlist owner is Spotify
            obj_in["id"] = "spotify"

        return SpotifyUser(id=obj_in["id"], name=owner_name)

    def from_user_followers(self, *, obj_in: Dict[str, Any]) -> Optional[SpotifyUser]:
        """
        Parse spotify user from a dict from a user's followers list
        Ex: {
            followers_count: 5
            following_count: 15
            image_url: "https://scontent-ort2-2.xx.fbcdn.net/v/t1.0-1/p320x320/12801550_1019289601470165_1814912048538690635_n.jpg?_nc_cat=104&ccb=2&_nc_sid=0c64ff&_nc_ohc=2-LV_47su3YAX9ZN3XV&_nc_oc=AQk0zOYue4rRCWPj0fZR_Irxt0ReV5hHgNYTtOkmELIlLOhodc6Q-fK1WblDQ8h9ew8&_nc_ht=scontent-ort2-2.xx&tp=6&oh=276b7d7e54dac1ca48c3e5ec34d9eeb0&oe=5FD03F0D"
            is_followed: true
            name: "John Doe"
            uri: "spotify:user:12102613074"
        }

        """
        if "uri" not in obj_in:
            return None

        obj_in["id"] = obj_in["uri"].split(":")[-1]
        if obj_in["id"] == "":
            obj_in["id"] = "spotify"

        return SpotifyUser(id=obj_in["id"], name=obj_in.get("name", None))


spotify_user = ParseSpotifyUser(SpotifyUser)

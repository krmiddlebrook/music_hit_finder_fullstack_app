from typing import Dict, Optional, Any

from app.spotify.parser.base import ParseBase
from app.schemas import Playlist, PlaylistCreate


class ParsePlaylist(ParseBase[Playlist, PlaylistCreate]):
    def from_playlist(self, *, obj_in: Dict[str, Any]) -> Optional[Playlist]:
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
        if "uri" not in obj_in:
            return None

        uri = obj_in["uri"].split(":")
        if len(uri) != 5:
            return None

        return Playlist(id=uri[-1], owner_id=uri[2], name=obj_in.get("name", None))


playlist = ParsePlaylist(Playlist)

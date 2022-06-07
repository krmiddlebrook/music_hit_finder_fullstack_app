from typing import Dict, List, Any, Optional
from copy import deepcopy
import datetime

from app.spotify.parser.base import ParseBase
from app.schemas import Artist, ArtistCreate, ArtistUpdate, ArtistLink, Genre


class ParseArtist(ParseBase[Artist, ArtistCreate]):
    def from_dict(self, *, obj_in: Dict[str, Any]) -> Optional[ArtistCreate]:
        copy_obj = deepcopy(obj_in)
        if not copy_obj.get("id", None) and not copy_obj.get("uri", None):
            return None

        if not copy_obj.get("id", None) and copy_obj.get("uri", None):
            copy_obj["id"] = self.uri2id(uri=copy_obj["uri"])

        if copy_obj.get("info", {}):
            copy_obj["name"] = copy_obj["info"].get("name", None)
            copy_obj["verified"] = copy_obj["info"].get("verified", None)
            is_inactive = copy_obj.get("upcoming_concerts", {}).get(
                "inactive_artist", None
            )
            if is_inactive is not None:
                copy_obj["active"] = not is_inactive

        if copy_obj.get("genres", []):
            if not isinstance(copy_obj["genres"][0], (Genre, dict)):
                copy_obj["genres"] = [Genre(id=g) for g in copy_obj["genres"]]
            # elif isinstance(copy_obj["genres"][0], Genre):
            # copy_obj["genres"] = [g.dict() for g in copy_obj["genres"]]

        if copy_obj.get("autobiography", {}).get("links", {}):
            copy_obj["links"] = []
            for ltype, l, in copy_obj["autobiography"]["links"].items():
                copy_obj["links"].append(
                    ArtistLink(
                        link=l,
                        artist_id=copy_obj["id"],
                        link_type=ltype,
                        date_added=datetime.date.today(),
                    )
                    # {
                    #     "link": l,
                    #     "artist_id": copy_obj["id"],
                    #     "link_type": ltype,
                    #     "date_added": datetime.date.today(),
                    # }
                )

        if isinstance(copy_obj.get("related_artists", {}), dict):
            related_artists = []
            if copy_obj.get("related_artists", {}).get("artists", []):
                for a in copy_obj.get("related_artists", {}).get("artists", []):
                    if a.get("uri", None):
                        related_artists.append(
                            Artist(
                                id=self.uri2id(uri=a["uri"]), name=a.get("name", None)
                            )
                        )
            copy_obj["related_artists"] = related_artists

        return ArtistCreate(**copy_obj)

    def from_artist_list(self, *, obj_in: List[Dict[str, Any]]) -> List[ArtistCreate]:
        """
        Parse artists from a list of artist results.
        """
        artists = []
        for art in obj_in:
            art_obj = self.from_dict(obj_in=art)
            if art_obj:
                artists.append(art_obj)

        return artists

    def from_track(
        self, *, obj_in: Dict[str, Any], include_album_artists: bool = True
    ) -> List[ArtistCreate]:
        """
        Parse all artists from a track result.

        Ex: {
            track: {
                album: {album_type: "album", artists:[{…},…], …}
                artists: [
                    {
                        external_urls: {spotify: "https://open.spotify.com/artist/..."}
                        href: "https://api.spotify.com/v1/artists/…"
                        id: "00QHEgqAQ8kNCVqBYOOp6O"
                        name: "Tuamie"
                        type: "artist"
                        uri: "spotify:artist:00QHEgqAQ8kNCVqBYOOp6O"
                    }, ...
                ]
                disc_number: 1
                duration_ms: 123027
                episode: false
                explicit: false
                external_ids: {isrc: "QZHN71924868"}
                external_urls: {spotify: "https://open.spotify.com/track/..."}
                href: "https://api.spotify.com/v1/tracks/…"
                id: "1lBh4VJsqBEw2mQmuDpq7m"
                is_local: false
                is_playable: true
                name: "Atlanta 93"
                popularity: 7
                preview_url: "https://p.scdn.co/mp3-preview/..."
                tags: []
                track: true
                track_number: 1
                type: "track"
                uri: "spotify:track:1lBh4VJsqBEw2mQmuDpq7m"
            }
        }
        """
        if obj_in.get("track", {}) and isinstance(obj_in.get("track", {}), dict):
            obj_in = obj_in["track"]

        artists = []
        # Add this track's track artists.
        artists += self.from_artist_list(obj_in=obj_in.get("artists", []))

        # Add this track's album artists.
        if include_album_artists:
            artists += self.from_album(obj_in=obj_in)

        return artists

    def from_album(self, *, obj_in: Dict[str, Any]) -> List[ArtistCreate]:
        if obj_in.get("album", {}).get("artists", []):
            return self.from_artist_list(obj_in=obj_in["album"]["artists"])
        else:
            return []

    def from_related_artists(
        self, *, obj_in: List[Dict[str, Any]]
    ) -> List[ArtistCreate]:
        for art in obj_in:
            if not art.get("uri", None):
                continue
            art["id"] = self.uri2id(uri=art["uri"])

        return self.from_artist_list(obj_in=obj_in)

    def from_artist_info(self, *, obj_in: Dict[str, Any]) -> Optional[ArtistCreate]:
        """
        Parse artist from spotify client artist info result.

        Ex: {
            biography: {text:"..."}
            creator_about: {monthlyListeners: 2763246}
            gallery: {images: [{uri: "https://i.scdn.co/image/…"},…]}
            header_image: {image: "https://i.scdn.co/image/…", offset: 0}
            info: {
                uri: "spotify:artist:2GHclqNVjqGuiE5mA7BEoc",
                name: "Common",
                verified: true,
                portraits:[{...}]
            }
            latest_release: {
                cover: {uri: "https://i.scdn.co/image/…"}
                day: 14
                month: 8
                name: "Kawa"
                track_count: 1
                uri: "spotify:album:1LiIQEA1QRLRtbK04SDewF"
                year: 2020
            }
            …
            upcoming_concerts: {inactive_artist: false}
            uri: "spotify:artist:2GHclqNVjqGuiE5mA7BEoc"
        }
        """
        if not obj_in.get("info", {}) or not obj_in.get("uri", None):
            return None

        return self.from_dict(obj_in=obj_in)


artist = ParseArtist(Artist)

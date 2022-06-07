from typing import Dict, Optional, Any, List
from copy import deepcopy

from app.spotify.parser.base import ParseBase
from app.schemas import Album, AlbumCreate

from app.spotify.utils import combine_date


class ParseAlbum(ParseBase[Album, AlbumCreate]):
    def from_dict(self, *, obj_in: Dict[str, Any]) -> Optional[AlbumCreate]:
        """
        Parse valid album object from dict. Works with album returned from
        Spotify API or the SPAPI album_playcount result.
        """
        copy_obj = deepcopy(obj_in)

        if copy_obj.get("album", {}):
            copy_obj = copy_obj["album"]

        if not copy_obj.get("id", None) and not copy_obj.get("uri", None):
            return None

        if not copy_obj.get("id", None) and copy_obj.get("uri", None):
            copy_obj["id"] = self.uri2id(uri=copy_obj["uri"])

        copy_obj["release_date"] = combine_date(copy_obj)

        if copy_obj.get("album_type", None):
            copy_obj["type"] = copy_obj["album_type"]

        if copy_obj.get("track_count", None):
            copy_obj["total_tracks"] = copy_obj["track_count"]

        if copy_obj.get("images", []):
            cover_dict = copy_obj["images"][-1]
            if cover_dict.get("url", None):
                copy_obj["cover"] = cover_dict["url"]
        elif isinstance(copy_obj.get("cover", None), dict):
            copy_obj["cover"] = copy_obj.get("cover", {}).get("uri", None)

        if copy_obj.get("label", None):
            if isinstance(copy_obj["label"], str):
                copy_obj["label_id"] = copy_obj.pop("label", None)

        # if copy_obj.get("artists", []):
        #     copy_obj["artists"] = artist.from_artist_list(obj_in=copy_obj["artists"])

        # if copy_obj.get("discs", []):
        #     copy_obj["tracks"] =
        # elif copy_obj.get("tracks", {}).get("items", []):
        #     copy_obj["tracks"] = copy_obj["tracks"]["items"]

        return AlbumCreate(**copy_obj)

    def from_album_playcount(self, *, obj_in: Dict[str, Any]) -> Optional[AlbumCreate]:
        """
        Parse album from album playcount result. This is primarly a convenience
        function, as it returns the result of the `from_dict` function.

        Ex: {
            uri: "spotify:album:61rwPIA5CVaw8Q2T6uOz6k",
            name: "Bummerland",
            artists: [
                {name: "AJR", uri: "spotify:artist:6s22t5Y3prQHyaHWUN1R1C"}
            ],
            copyrights: [
                "© ℗ 2020 AJR Productions, LLC under exclusive license to S-Curve Records"  # noqa: E501
            ],
            cover: {uri: "https://i.scdn.co/image/…"},
            day: 31,
            discs: [
                {
                    number: 1, name: "",
                    tracks: [ 
                        {
                            artists: [{name: "AJR", uri: "spotify:artist:…",…}]
                            duration: 189115
                            explicit: false
                            name: "Bummerland"
                            number: 1
                            playable: true
                            playcount: 3859306
                            popularity: 68
                            uri: "spotify:track:33n9hKYymXgXV0p6j2zYp9",
                        },…
                    ]
                },{…},…
            ],
            label: "S-Curve Records",
            month: 8,
            related: {
                releases: [
                    {
                        uri: "spotify:album:02tIakRsIFGW8sO4pBtJgj",
                        name: "Neotheater",
                        …
                    },…
                ]
            },
            track_count: 1,
            type: "single",
            year: 2020
        }
        """
        return self.from_dict(obj_in=obj_in)

    def from_album(self, *, obj_in: Dict[str, Any]) -> Optional[AlbumCreate]:
        """
        Parse valid album object from spotify api album result. This is
        primarly a convenience function, as it returns the result of
        the `from_dict` function.
        """
        return self.from_dict(obj_in=obj_in)

    def from_track(self, *, obj_in: Dict[str, Any]) -> Optional[AlbumCreate]:
        """
        Parse album from a track result.
        
        Ex: {
            track: {
                album: {
                    album_type: "album"
                    artists: [{external_urls: {spotify: "https://open.spotify.com/artist/…"},…}]
                    external_urls: {spotify: "https://open.spotify.com/album/…"}
                    href: "https://api.spotify.com/v1/albums/…"
                    id: "6AVRxSnm8TaiVDBkZR7yH0"
                    images: [{height: 640, url: "https://i.scdn.co/image/…", width: 640},…]
                    name: "But You Don't Hear Me Though"
                    release_date: "2019-10-05"
                    release_date_precision: "day"
                    total_tracks: 16
                    type: "album"
                    uri: "spotify:album:6AVRxSnm8TaiVDBkZR7yH0"
                }
                artists: [{external_urls: {spotify: "https://open.spotify.com/artist/…"},…}]
                disc_number: 1
                duration_ms: 123027
                episode: false
                explicit: false
                external_ids: {isrc: "QZHN71924868"}
                external_urls: {spotify: "https://open.spotify.com/track/…"}
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
        if obj_in.get("track", {}):
            if isinstance(obj_in["track"], dict):
                if obj_in["track"].get("album", {}):
                    return self.from_album(obj_in=obj_in["track"]["album"])
            else:
                if obj_in.get("album", {}):
                    return self.from_album(obj_in=obj_in["album"])
        else:
            return None

    def _from_releases(
        self, *, obj_in: List[Dict[str, Any]], release_type: str
    ) -> List[AlbumCreate]:
        """
        Parse tracks from a release group list returned by the SPAPI artist_info endpoint.

        Ex: 
        [
            {
                cover: {uri: "https://i.scdn.co/image/…"}
                day: 15
                discs: [
                    {
                        number: 1,
                        name: "",
                        tracks: [
                            {
                                artists: [
                                    {
                                        name: "Elijah Nang",
                                        uri: "spotify:artist:0yIO6HI875mLzamqmjjFFU"    # noqa: E501
                                    },
                                    …
                                ]
                                duration: 198518
                                explicit: false
                                name: "A Hero Is Born"
                                number: 1
                                playable: true
                                playcount: 122925
                                popularity: 36
                                uri: "spotify:track:4SJJkTyFoNcXQYfMr9x3or"
                            },…
                        ]
                    },…
                ]
                month: 5
                name: "Gaijin II Tale of Rai"
                track_count: 20
                uri: "spotify:album:79ynbZwBXsmdFZw8Oa0FMK"
                year: 2020
            },
            {…},
            …
        ]
        """
        albums = []
        for release in obj_in:
            if not release.get("uri", None):
                continue
            release["type"] = release_type
            album = self.from_dict(obj_in=release)
            if album:
                albums.append(album)

        return albums

    def from_releases(
        self,
        *,
        obj_in: Dict[str, Any],
        singles: bool = True,
        albums: bool = True,
        compilations: bool = False,
        appears_on: bool = False,
    ) -> List[AlbumCreate]:
        """
        Parse tracks from a release result returned by the SPAPI artist_info endpoint.

        Ex: {
            albums: {
                releases: [
                    {
                        cover: {uri: "https://i.scdn.co/image/…"}
                        day: 15
                        discs: [
                            {
                                number: 1,
                                name: "",
                                tracks: [
                                    {
                                        artists: [
                                            {
                                                name: "Elijah Nang",
                                                uri: "spotify:artist:0yIO6HI875mLzamqmjjFFU"    # noqa: E501
                                            },
                                            …
                                        ]
                                        duration: 198518
                                        explicit: false
                                        name: "A Hero Is Born"
                                        number: 1
                                        playable: true
                                        playcount: 122925
                                        popularity: 36
                                        uri: "spotify:track:4SJJkTyFoNcXQYfMr9x3or"
                                    },…
                                ]
                            },…
                        ]
                        month: 5
                        name: "Gaijin II Tale of Rai"
                        track_count: 20
                        uri: "spotify:album:79ynbZwBXsmdFZw8Oa0FMK"
                        year: 2020
                    },…
                ],
                total_count: 5
            }
            appears_on: {,…}
            compilations: {total_count: 0}
            singles: {
                releases: [{…},…],
                total_count: 7
            }
        }
        """
        albums_list = []
        if singles and obj_in.get("singles", {}):
            albums_list += self._from_releases(
                obj_in=obj_in["singles"].get("releases", []), release_type="single"
            )

        if albums and obj_in.get("albums", {}):
            albums_list += self._from_releases(
                obj_in=obj_in["albums"].get("releases", []), release_type="album"
            )

        if compilations and obj_in.get("compilations", {}):
            albums_list += self._from_releases(
                obj_in=obj_in["compilations"].get("releases", []),
                release_type="compilation",
            )

        if appears_on and obj_in.get("appears_on", {}):
            albums_list += self._from_releases(
                obj_in=obj_in["appears_on"].get("releases", []),
                release_type="appears_on",
            )

        return albums_list


album = ParseAlbum(AlbumCreate)

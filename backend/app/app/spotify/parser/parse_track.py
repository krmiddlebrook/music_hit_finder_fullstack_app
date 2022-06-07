from typing import Dict, Optional, Any, List
from copy import deepcopy

from app.spotify.parser.base import ParseBase
from app.schemas import Track, TrackCreate, TrackPlaycount

# from .parse_artist import artist
# from .parse_album import album


class ParseTrack(ParseBase[Track, TrackCreate]):
    def from_dict(
        self,
        *,
        obj_in: Dict[str, Any],
        album_id: Optional[str] = None,
        disc_num: Optional[int] = 1,
    ) -> Optional[TrackCreate]:
        """
        Parse valid Track object from dict.
        """
        if (not obj_in.get("id", None) and not obj_in.get("uri", None)) or (
            not obj_in.get("album", {}).get("id", None)
            and not obj_in.get("album_id", None)
            and not album_id
        ):
            return None

        copy_obj = deepcopy(obj_in)

        if not copy_obj.get("id", None):
            copy_obj["id"] = self.uri2id(copy_obj["uri"])

        if copy_obj.get("duration", None):
            copy_obj["duration_ms"] = copy_obj.get("duration", None)

        if copy_obj.get("track_number", None) and copy_obj.get("disc_number", None):
            copy_obj["track_number"] = (
                copy_obj["track_number"] * copy_obj["disc_number"]
            )
        elif copy_obj.get("number", None) and disc_num:
            copy_obj["track_number"] = copy_obj["number"] * disc_num

        if not copy_obj.get("isrc", None) and copy_obj.get("external_ids", {}).get(
            "isrc", None
        ):
            copy_obj["isrc"] = copy_obj["external_ids"]["isrc"]

        if not copy_obj.get("album_id", None):
            if album_id:
                copy_obj["album_id"] = album_id
            elif obj_in.get("album", {}).get("id", None):
                copy_obj["album_id"] = copy_obj["album"]["id"]

        # if copy_obj.get("album", {}):
        #     copy_obj["album"] = album.from_dict(obj_in=copy_obj["album"])

        # if copy_obj.get("artists", []):
        #     copy_obj["artists"] =

        return TrackCreate(**copy_obj)

    def from_playlist_track(self, *, obj_in: Dict[str, Any]) -> Optional[TrackCreate]:
        """
        Parse track from a playlist result or a spotify user profile view Track result.
        
        Ex: {
            album: {album_type: "album",…}
            artists: [{external_urls: {spotify: "https://open.spotify.com/artist/…"},…}]
            disc_number: 1
            duration_ms: 123027
            episode: false
            explicit: false
            external_ids: {isrc: "QZHN71924868"}
            external_urls: {spotify: "https://open.spotify.com/track/…"}
            href: "https://api.spotify.com/v1/tracks/1lBh4VJsqBEw2mQmuDpq7m"
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
        """
        return self.from_dict(obj_in=obj_in)

    def from_playlist_tracks(
        self, *, obj_in: List[Dict[str, Any]]
    ) -> List[TrackCreate]:
        """
        Parse list of playlist tracks into valid track objects
        """
        tracks = []
        for t in obj_in:
            t = self.from_playlist_track(obj_in=t["track"])
            if t:
                tracks.append(t)

        return tracks

    def from_track_playcount_list(
        self, *, obj_in: List[TrackPlaycount]
    ) -> List[TrackCreate]:
        """
        Convert list of TrackPlaycount objects to valid Track objects
        """
        raise NotImplementedError

    def from_track_list(
        self, *, obj_in: List[Dict[str, Any]], disc_num: int = 1, album_id: str = None
    ) -> List[TrackCreate]:
        """
        Parse track objects from SPAPI album track list result.

        Ex:
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
        """
        # print("FROM TRACK LIST (BEFORE): ")
        # print(obj_in)

        tracks = []
        for track in obj_in:
            t = self.from_dict(obj_in=track, album_id=album_id, disc_num=disc_num)
            if t:
                tracks.append(t)

        # print("FROM TRACK LIST (after): ")
        # print(tracks)

        return tracks

    def from_discs(
        self, *, obj_in: List[Dict[str, Any]], album_id: str
    ) -> List[TrackCreate]:
        """
        Parse track playcount objects from SPAPI album disc list result.
        
        Ex: [
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
            },
            {…},
            …
        ]
        """
        tracks = []
        for disc_num, disc in enumerate(obj_in):
            tracks += self.from_track_list(
                obj_in=disc.get("tracks", []), disc_num=disc_num, album_id=album_id
            )

        return tracks

    def _from_releases(self, *, obj_in: List[Dict[str, Any]]) -> List[TrackCreate]:
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
        tracks = []
        for release in obj_in:
            if release.get("uri", None) and release.get("discs", None):
                album_id = self.uri2id(release["uri"])
                tracks += self.from_discs(obj_in=release["discs"], album_id=album_id)

        return tracks

    def from_releases(
        self,
        *,
        obj_in: Dict[str, Any],
        singles: bool = True,
        albums: bool = True,
        compilations: bool = False,
        appears_on: bool = False,
    ) -> List[TrackCreate]:
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
        tracks = []
        if singles and obj_in.get("singles", {}):
            tracks += self._from_releases(obj_in=obj_in["singles"].get("releases", []))

        if albums and obj_in.get("albums", {}):
            tracks += self._from_releases(obj_in=obj_in["albums"].get("releases", []))

        if compilations and obj_in.get("compilations", {}):
            tracks += self._from_releases(
                obj_in=obj_in["compilations"].get("releases", [])
            )

        if appears_on and obj_in.get("appears_on", {}):
            tracks += self._from_releases(
                obj_in=obj_in["appears_on"].get("releases", [])
            )

        return tracks

    def from_artist_info(
        self, *, obj_in: Dict[str, Any], include_releases: str = "singles,albums"
    ) -> List[TrackCreate]:
        """
        Parse track from artist info result from the SPAPI.
        
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
            merch: {items: [{name: "BE Vinyl Record",…},…]}
            monthly_listeners: {listener_count: 2763246}
            published_playlists: {playlists: [,…]}
            related_artists: {artists: [{…},…]}
            releases: {
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
            top_tracks: {tracks: [{…},…]}
            upcoming_concerts: {inactive_artist: false}
            uri: "spotify:artist:2GHclqNVjqGuiE5mA7BEoc"
        }
        """
        tracks = []
        if not obj_in.get("releases", []):
            return tracks

        release_types = {rtype: True for rtype in include_releases.split(",")}

        return self.from_releases(obj_in=obj_in["releases"], **release_types)

    def from_album_playcount(self, *, obj_in: Dict[str, Any]) -> List[TrackCreate]:
        tracks = []
        if not obj_in.get("uri", None) or not obj_in.get("discs", []):
            return tracks

        album_id = self.uri2id(uri=obj_in["uri"])
        return self.from_discs(obj_in=obj_in["discs"], album_id=album_id)


track = ParseTrack(Track)

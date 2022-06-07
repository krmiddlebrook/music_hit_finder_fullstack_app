from typing import Dict, Any, Optional

import requests
from celery.utils.log import get_task_logger
from .utils import combine_date
from app.core.config import settings

logger = get_task_logger(__name__)


class SpAPI(object):
    """ 
    A class to access a self-hosted Spotify client internal API. 
    """

    def __init__(self, base_url=settings.SPAPI_URL):
        # babase_urlse url
        self.base_url = base_url
        self.artist_endpoints = {
            "info": self.artist_info,
            "insights": self.artist_insights,
            "about": self.artist_about,
        }

    def _request(
        self, url: str, conn_timeout: int = 3, read_timeout: int = 10
    ) -> Optional[Dict[str, Any]]:
        """ Helper method to process a SpAPI request. """
        try:
            resp = requests.get(url, timeout=(conn_timeout, read_timeout))
            if resp.status_code == 200:
                result = resp.json()
                if result.get("success", False):
                    result = result.get("data", {})
                else:
                    result = None
            else:
                resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Invalid request for url: {url} \n Error: {e}")
            result = None
        finally:
            return result

    def parse_album(
        data,
        keys=["id", "releaseDate", "trackCount", "tracks", "label"],
        rem_track_keys=["playable", "uri"],
    ) -> Dict[str, Any]:
        """ 
        Deprecated!!! Parse album data.

        Returns:
            A dict containing the cleaned album metadata.
        """
        # Store the cleaned album metadata.
        cdata = {}
        for k in keys:
            if k == "id":
                cdata[k] = data["uri"].split(":")[-1]
            elif k == "releaseDate":
                cdata[k] = combine_date(data)
            elif k == "trackCount":
                cdata[k] = data["track_count"]
            elif k == "tracks":
                # Store the cleaned tracks metadata
                ctracks = []
                for disc in data["discs"]:
                    for track in disc:
                        track["number"] *= disc.get("number", 1)
                        track["id"] = track["uri"].split(":")[-1]
                        # Remove multiple keys from track dict.
                        [track.pop(rkey) for rkey in rem_track_keys]
                        ctracks.append(track)
                cdata[k] = ctracks
            else:
                cdata[k] = data[k]
        return cdata

    def album_playcount(
        self, album_id: str, conn_timeout: int = 3, read_timeout: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Get album metadata, including track playcounts.

        Ex of a successful request:
        {
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
            year: 2020,
            additional: {releases: [{uri: "spotify:album:42wvKYHFezpmDuAP43558f", name: "Scorpion",…}]}
        }
        """
        url = self.base_url + "albumPlayCount?albumid=" + album_id
        return self._request(url, conn_timeout, read_timeout)

    def artist(
        self, artist_id: str, *, conn_timeout: int = 3, read_timeout: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve data about an artist.
        """
        result = {}
        result["artist_info"] = self.artist_info(
            artist_id, conn_timeout=conn_timeout, read_timeout=read_timeout
        )
        result["artist_insights"] = self.artist_insights(
            artist_id, conn_timeout=conn_timeout, read_timeout=read_timeout
        )
        return result

    def artist_info(
        self, artist_id: str, *, conn_timeout: int = 3, read_timeout: int = 10
    ) -> Optional[Dict[str, Any]]:
        """ 
        Retrieve info about an artist.

        Ex:
        {
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
            related_artists: {
                artists: [
                    {
                        uri: "spotify:artist:0Mz5XE0kb1GBnbLQm2VbcO",
                        name: "Mos Def",
                        portraits: [{uri: "https://i.scdn.co/image/…"}]
                    },…
                ]
            }
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
        url = self.base_url + "artistInfo?artistid=" + artist_id
        return self._request(url, conn_timeout, read_timeout)

    def artist_insights(
        self, artist_id: str, *, conn_timeout=3, read_timeout=10
    ) -> Optional[Dict[str, Any]]:
        """ 
        Retrieve insights data about an artist.

        Ex:
        {
            artistGid: "1266ba140e944c88937dd382bd47e422"
            autobiography: {
                body: "Samurai beatsmith since 2010. ",
                urls: [],
                links: {
                    twitter: "https://twitter.com/Nangfood",
                    instagram: "https://instagram.com/elijahnang/",
                    …
                }
            }
            cities: [
                {country: "US", region: "CA", city: "Los Angeles", listeners: 4960},…   # noqa: E501
            ]
            followerCount: 15791
            followingCount: 0
            globalChartPosition: 0
            headerImage: {id: "78cc4e73d0ac4e749dd9c907bfe61c20",…}
            images: [
                {
                    height: 640
                    id: "587b0f7c307840c9825fc2ed32a91aa3"
                    uri: "https://i.scdn.co/image/…"
                    width: 640
                },…
            ]
            imagesCount: 3
            mainImageUrl: "https://i.scdn.co/image/…"
            monthlyListeners: 487020
            monthlyListenersDelta: -19470
            name: "Elijah Nang"
            playlists: {
                entries: [
                    {
                        imageUrl: "https://i.scdn.co/image/…"
                        listeners: 0
                        name: "Chill Lofi Study Beats"
                        owner: {name: "Spotify", uri: "spotify:user:spotify"}
                        uri: "spotify:user:spotify:playlist:37i9dQZF1DX8Uebhn9wzrS"
                    }
                ],
                userCanEdit: false
            }
        }
        """
        url = self.base_url + "artistInsights?artistid=" + artist_id
        resp = self._request(url, conn_timeout, read_timeout)
        if resp:
            resp["id"] = artist_id

        return resp

    def artist_about(self, artist_id: str, conn_timeout=3, read_timeout=10):
        """ 
        Retrieve mini version of the info about an artist.
        """
        url = self.base_url + "artistAbout?artistid=" + artist_id
        return self._request(url, conn_timeout, read_timeout)


spapi = SpAPI(base_url=settings.SPAPI_URL)

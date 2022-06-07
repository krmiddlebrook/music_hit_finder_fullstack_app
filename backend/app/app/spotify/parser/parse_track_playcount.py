from typing import Dict, Optional, List, Any
import datetime
from copy import deepcopy

from app.spotify.parser.base import ParseBase
from app.schemas import TrackPlaycount, TrackPlaycountCreate


class ParseTrackPlaycount(ParseBase[TrackPlaycount, TrackPlaycountCreate]):
    def make_id(self, *, track_id: str, date: Optional[datetime.date] = None) -> str:
        """
        Create valid track_playcount id.
        """
        if not date:
            date = datetime.date.today().strftime("%Y-%m-%d")
        else:
            date = date.strftime("%Y-%m-%d")
        return f"{track_id}_{date}"

    def from_dict(self, *, obj_in: List[Dict[str, Any]]) -> Optional[TrackPlaycount]:
        """
        Parse valid TrackPlaycount object from dict.

        Ex Input: {
            artists: [{name: "AJR", uri: "spotify:artist:…",…}]
            duration: 189115
            explicit: false
            name: "Bummerland"
            number: 1
            playable: true
            playcount: 3859306
            popularity: 68
            uri: "spotify:track:33n9hKYymXgXV0p6j2zYp9",
        }
        """
        copy_obj = deepcopy(obj_in)
        if not copy_obj.get("uri", None) or not copy_obj.get("playcount", None):
            return

        tid = self.uri2id(copy_obj["uri"])
        if not tid:
            return

        copy_obj["track_id"] = tid
        copy_obj["date"] = datetime.date.today()
        copy_obj["id"] = self.make_id(
            track_id=copy_obj["track_id"], date=copy_obj["date"]
        )

        return TrackPlaycount(**copy_obj)

    def from_track_list(self, *, obj_in: List[Dict[str, Any]]) -> List[TrackPlaycount]:
        """
        Parse track playcount objects from SPAPI album track list result.

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
        track_playcount_objs = []
        for track in obj_in:
            tp = self.from_dict(obj_in=track)
            if tp:
                track_playcount_objs.append(tp)

        return track_playcount_objs

    def from_discs(self, *, obj_in: List[Dict[str, Any]]) -> List[TrackPlaycount]:
        """
        Parse track playcount objects from SPAPI album disc list result
        """
        track_playcount_objs = []
        for disc in obj_in:
            track_playcount_objs += self.from_track_list(obj_in=disc.get("tracks", []))

        return track_playcount_objs

    def from_album(self, *, obj_in: Dict[str, Any]) -> List[TrackPlaycount]:
        """
        Parse track playcount objects from SPAPI album result.

        Ex:
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
                },
                {number: 2, name: "", tracks:[…],…},…
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
        # print("*" * 50)
        # print(obj_in)
        # print("*" * 50)
        track_playcount_objs = []
        if not obj_in.get("discs", []):
            return track_playcount_objs

        return self.from_discs(obj_in=obj_in["discs"])


track_playcount = ParseTrackPlaycount(TrackPlaycount)

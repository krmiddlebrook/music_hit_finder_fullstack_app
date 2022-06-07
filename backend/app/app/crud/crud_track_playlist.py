from typing import Optional, List, Dict
from collections import defaultdict

from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.crud.base import CRUDBase
from app.models.track_playlist import Track_Playlist
from app.schemas.track_playlist import TrackPlaylistCreate, TrackPlaylistUpdate


class CRUDTrackPlaylist(
    CRUDBase[Track_Playlist, TrackPlaylistCreate, TrackPlaylistUpdate]
):
    def get(
        self, db: Session, *, track_id: str, playlist_id: str
    ) -> Optional[Track_Playlist]:
        return (
            db.query(Track_Playlist)
            .filter(
                Track_Playlist.track_id == track_id,
                Track_Playlist.playlist_id == playlist_id,
            )
            .first()
        )

    def create_multi_from_playlist_ids(
        self, db: Session, *, playlist_ids_track_ids: Dict[str, set]
    ) -> bool:
        """
        Create playlist_id <> track_id pairs to the db.
        `playlist_ids_track_ids` is a dict where keys are playlist_ids and values are
        sets with the associated track_ids.
        """
        db_pairs = defaultdict(set)
        playlist_ids = list(playlist_ids_track_ids.keys())
        for db_tp in (
            db.query(Track_Playlist)
            .filter(Track_Playlist.playlist_id.in_(playlist_ids))
            .all()
        ):
            db_pairs[db_tp.playlist_id].add(db_tp.track_id)

        canidate_pairs = []
        for pid, tids in playlist_ids_track_ids.items():
            for tid in tids:
                if tid not in db_pairs[pid]:
                    canidate_pairs.append(
                        jsonable_encoder(
                            TrackPlaylistCreate(playlist_id=pid, track_id=tid)
                        )
                    )
        return super().create_multi(db, objs_in=canidate_pairs)


track_playlist = CRUDTrackPlaylist(Track_Playlist)

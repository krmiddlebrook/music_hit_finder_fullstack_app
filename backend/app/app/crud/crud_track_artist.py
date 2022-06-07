from typing import Optional, List, Dict
from collections import defaultdict

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.track_artist import Track_Artist
from app.schemas.track_artist import TrackArtistCreate, TrackArtistUpdate


class CRUDTrackArtist(CRUDBase[Track_Artist, TrackArtistCreate, TrackArtistUpdate]):
    # TODO: functions to retrieve playlist by owner and by name
    def get(
        self, db: Session, *, track_id: str, artist_id: str
    ) -> Optional[Track_Artist]:
        return (
            db.query(Track_Artist)
            .filter(
                Track_Artist.track_id == track_id, Track_Artist.artist_id == artist_id
            )
            .first()
        )

    def create_multi_from_track_ids(
        self, db: Session, *, track_ids_artist_ids: Dict[str, set]
    ) -> bool:
        """
        Push track_id <> artist_id pairs to the db.
        `track_ids_artist_ids` is a dict where keys are track_ids and values are
        sets with the associated artist ids.
        """
        db_pairs = defaultdict(set)
        track_ids = list(track_ids_artist_ids.keys())
        for db_ta in (
            db.query(Track_Artist).filter(Track_Artist.track_id.in_(track_ids)).all()
        ):
            db_pairs[db_ta.track_id].add(db_ta.artist_id)

        canidate_pairs = []
        for tid, aids in track_ids_artist_ids.items():
            for aid in aids:
                if aid not in db_pairs[tid]:
                    canidate_pairs.append(
                        TrackArtistCreate(track_id=tid, artist_id=aid).dict()
                    )
        return super().create_multi(db, objs_in=canidate_pairs)


track_artist = CRUDTrackArtist(Track_Artist)

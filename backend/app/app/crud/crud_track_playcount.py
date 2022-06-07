from typing import Optional, List
from sqlalchemy.orm import Session
import datetime
from app.crud.base import CRUDBase
from app.models.track_playcount import Track_Playcount
from app.models.track import Track
from app.schemas.track_playcount import (
    TrackPlaycountCreate,
    TrackPlaycountUpdate,
)


class CRUDTrackPlaycount(
    CRUDBase[Track_Playcount, TrackPlaycountCreate, TrackPlaycountUpdate]
):
    def get_by_track_id(
        self, db: Session, track_id: str
    ) -> Optional[List[Track_Playcount]]:
        return (
            db.query(Track_Playcount).filter(Track_Playcount.track_id == track_id).all()
        )

    def get_by_track_id_and_date(
        self, db: Session, *, track_id: str, date: datetime.date
    ) -> Optional[Track_Playcount]:
        return (
            db.query(Track_Playcount)
            .filter(Track_Playcount.track_id == track_id, Track_Playcount.date == date)
            .first()
        )

    def get_by_track_ids_and_date(
        self, db: Session, *, track_ids: List[str], date: datetime.date
    ) -> List[Track_Playcount]:
        """
        Retrieve a list of track_playcount objects in the db given a set of track_ids
        and the playcount date.
        """
        db_objs = (
            db.query(Track_Playcount)
            .filter(
                Track_Playcount.track_id.in_(track_ids), Track_Playcount.date == date
            )
            .all()
        )
        if not db_objs:
            db_objs = []
        return db_objs

    def get_by_album_id_and_date(
        self, db: Session, album_id: str, date: datetime.date
    ) -> Optional[List[Track_Playcount]]:
        """
        Retrieve a list of track_playcount objects in the db associated with the given
        album_id and the playcount date.
        """
        return (
            db.query(Track_Playcount)
            .join(Track_Playcount.track)
            .filter(Track.album_id == album_id, Track_Playcount.date == date)
            .all()
        )


track_playcount = CRUDTrackPlaycount(Track_Playcount)

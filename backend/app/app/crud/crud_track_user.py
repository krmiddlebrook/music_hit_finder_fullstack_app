from typing import Optional, List

from sqlalchemy.orm import Session
from celery.utils.log import get_task_logger

from app.crud.base import CRUDBase
from app.models.track_user import Track_User
from app.schemas.track_user import TrackUserCreate, TrackUserUpdate

logger = get_task_logger(__name__)


class CRUDTrackUser(CRUDBase[Track_User, TrackUserCreate, TrackUserUpdate]):
    def create(
        self,
        db: Session,
        *,
        track_id: str,
        user_id: str,
        top_track: Optional[bool] = False,
        source: Optional[str] = None
    ) -> Track_User:
        obj_in = TrackUserCreate(
            track_id=track_id, user_id=user_id, top_track=top_track, source=source
        )
        return super().create(db, obj_in=obj_in, refresh=True)

    def get(self, db: Session, *, track_id: str, user_id: str) -> Optional[Track_User]:
        return (
            db.query(Track_User)
            .filter(Track_User.track_id == track_id, Track_User.user_id == user_id)
            .first()
        )

    def get_multi_by_user(
        self, db: Session, *, user_spotify_id: str
    ) -> List[Track_User]:
        """
        Retrieve track user objects associated with the given user's spotify id.
        """
        return db.query(Track_User).filter(Track_User.user_id == user_spotify_id).all()


track_user = CRUDTrackUser(Track_User)

from typing import Optional, List

from sqlalchemy.orm import Session
from celery.utils.log import get_task_logger

from app.crud.base import CRUDBase
from app.models.track_distance import Track_Distance
from app.schemas.track_distance import (
    TrackDistance,
    TrackDistanceCreate,
    TrackDistanceUpdate,
)
from app.core.config import settings

logger = get_task_logger(__name__)


class CRUDTrackDistance(
    CRUDBase[Track_Distance, TrackDistanceCreate, TrackDistanceUpdate]
):
    def get(
        self,
        db: Session,
        *,
        t1_id: str,
        t2_id: str,
        model_id: Optional[str] = settings.MODEL_ID,
        distance_type: Optional[str] = settings.DISTANCE_TYPE,
    ) -> Optional[Track_Distance]:
        """
        Retrieve the distance measure for the given track ids pair. 
        """
        if t1_id < t2_id:
            src_id = t1_id
            tgt_id = t2_id
        else:
            src_id = t2_id
            tgt_id = t1_id

        return (
            db.query(Track_Distance)
            .filter(
                Track_Distance.src_id == src_id,
                Track_Distance.tgt_id == tgt_id,
                Track_Distance.model_id == model_id,
                Track_Distance.distance_type == distance_type,
            )
            .first()
        )

    def get_by_track_pair(
        self, db: Session, *, t1_id: str, t2_id: str,
    ) -> Optional[List[Track_Distance]]:
        """
        Retrieve a list of distances for the given track ids pair.
        """
        if t1_id < t2_id:
            src_id = t1_id
            tgt_id = t2_id
        else:
            src_id = t2_id
            tgt_id = t1_id

        return (
            db.query(Track_Distance)
            .filter(Track_Distance.src_id == src_id, Track_Distance.tgt_id == tgt_id)
            .all()
        )

    def create(self, db: Session, *, obj_in: TrackDistanceCreate) -> Track_Distance:
        # Id is <src_id>_<tgt_id>_<model_id>_<distance_type>
        # Note: src_id < tgt_id
        if obj_in.t1_id < obj_in.t2_id:
            d_id = f"{obj_in.t1_id}_{obj_in.t2_id}"
            src_id = obj_in.t1_id
            tgt_id = obj_in.t2_id
        else:
            d_id = f"{obj_in.t2_id}_{obj_in.t1_id}"
            src_id = obj_in.t2_id
            tgt_id = obj_in.t1_id
        d_id = f"{d_id}_{obj_in.model_id}_{obj_in.distance_type}"
        obj_in = TrackDistance(
            id=d_id,
            src_id=src_id,
            tgt_id=tgt_id,
            model_id=obj_in.model_id,
            distance_type=obj_in.distance_type,
            distance=obj_in.distance,
        )
        return super().create(db, obj_in=obj_in, refresh=True)


track_distance = CRUDTrackDistance(Track_Distance)

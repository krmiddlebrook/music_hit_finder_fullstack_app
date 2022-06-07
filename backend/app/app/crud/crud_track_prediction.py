from typing import Optional, List, Any
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import text, Integer, String, Float, Boolean, desc

from app.crud.base import CRUDBase
from app.models.track_prediction import Track_Prediction
from app.schemas.track_prediction import TrackPredictionCreate, TrackPredictionUpdate
from app import models


class CRUDTrackPrediction(
    CRUDBase[Track_Prediction, TrackPredictionCreate, TrackPredictionUpdate]
):
    def get(
        self, db: Session, *, track_id: str, model_id: str,
    ) -> Optional[Track_Prediction]:
        return (
            db.query(Track_Prediction)
            .filter(
                Track_Prediction.track_id == track_id,
                Track_Prediction.model_id == model_id,
            )
            .first()
        )

    def get_by_track_id(
        self, db: Session, *, track_id: str, skip: int = 0, limit: int = 100,
    ) -> List[Track_Prediction]:
        return (
            db.query(Track_Prediction)
            .filter(Track_Prediction.track_id == track_id)
            .order_by(desc(Track_Prediction.date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_model_id(
        self, db: Session, *, model_id: str, skip: int = 0, limit: int = 100
    ) -> Optional[List[Track_Prediction]]:
        return (
            db.query(Track_Prediction)
            .filter(Track_Prediction.model_id == model_id)
            .order_by(desc(Track_Prediction.probability))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_hit_tracks(
        self, db: Session, *, model_id: str, skip: int = 0, limit: int = 10_000
    ) -> Optional[List[Track_Prediction]]:
        return (
            db.query(Track_Prediction)
            .filter(
                Track_Prediction.model_id == model_id,
                Track_Prediction.prediction == 1.0,
            )
            .order_by(desc(Track_Prediction.probability))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_probability(
        self,
        db: Session,
        *,
        model_id: str,
        min_prob: float = 0.5,
        max_prob: float = 1.0,
        skip: int = 0,
        limit: int = 10_000,
    ) -> Optional[List[Track_Prediction]]:
        return (
            db.query(Track_Prediction)
            .filter(
                Track_Prediction.model_id == model_id,
                Track_Prediction.probability >= min_prob,
                Track_Prediction.probability <= max_prob,
            )
            .order_by(desc(Track_Prediction.probability))
            .offset(skip)
            .limit(limit)
            .all()
        )


track_prediction = CRUDTrackPrediction(Track_Prediction)

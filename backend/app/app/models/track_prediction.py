from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import Column, ForeignKey, String, Float, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .track import Track  # noqa: F401


class Track_Prediction(Base):
    track_id = Column(String, ForeignKey("track.id"), primary_key=True, index=True)
    model_id = Column(String, ForeignKey("ml_model.id"), primary_key=True, index=True)
    date = Column(DateTime, default=datetime.now, index=True, nullable=False)
    prediction = Column(Float, nullable=False)
    probability = Column(Float, nullable=False)
    track = relationship("Track", back_populates="predictions")

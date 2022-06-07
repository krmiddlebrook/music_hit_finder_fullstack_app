from typing import TYPE_CHECKING
from datetime import date

from sqlalchemy import Column, ForeignKey, Integer, BIGINT, String, Date
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .track import Track  # noqa: F401


class Track_Playcount(Base):
    # __tablename__ = "tracks_playcounts"
    id = Column(String, primary_key=True, index=True)  # Format: <track_id>_<date>
    track_id = Column(String, ForeignKey("track.id"), index=True)
    date = Column(Date(), default=date.today, index=True, nullable=False)
    playcount = Column(BIGINT, nullable=False)
    popularity = Column(Integer)
    track = relationship("Track", back_populates="playcounts")

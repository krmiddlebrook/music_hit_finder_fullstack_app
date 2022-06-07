from typing import TYPE_CHECKING
from datetime import date

from sqlalchemy import Column, String, Integer, ForeignKey, Date
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .artist import Artist  # noqa: F401


class Artist_Stat(Base):
    # __tablename__ = "artists_stats"
    # Id is <artist_id>_<date>
    id = Column(String, primary_key=True, index=True)
    artist_id = Column(String, ForeignKey("artist.id"), index=True, nullable=False)
    date = Column(Date(), default=date.today, index=True, nullable=False)
    followers_count = Column(Integer, nullable=False)
    following_count = Column(Integer)
    monthly_listeners = Column(Integer)
    world_rank = Column(Integer, default=0)
    artist = relationship("Artist", back_populates="stats")

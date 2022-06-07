from typing import TYPE_CHECKING
from datetime import date

from sqlalchemy import Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .playlist import Playlist  # noqa: F401


class Playlist_Followers_Count(Base):
    # __tablename__ = "playlists_followers_counts"
    id = Column(String, primary_key=True, index=True)  # <playlist_id>_<date>
    playlist_id = Column(String, ForeignKey("playlist.id"), index=True, nullable=False)
    date = Column(Date(), default=date.today, index=True, nullable=False)
    followers_count = Column(Integer, nullable=False)
    playlist = relationship("Playlist", back_populates="followers_counts")

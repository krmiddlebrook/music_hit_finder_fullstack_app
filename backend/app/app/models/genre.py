from typing import TYPE_CHECKING

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .artist import Artist  # noqa: F401


class Genre(Base):
    # __tablename__ = "genres"
    # Id is the genre, e.g., id = "rock"
    id = Column(String, primary_key=True, index=True)
    artists = relationship("Artist", secondary="genre_artist", back_populates="genres")

from typing import TYPE_CHECKING
from datetime import date

from sqlalchemy import Column, String, ForeignKey, Date
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .artist import Artist  # noqa: F401


class Artist_Link(Base):
    # __tablename__ = "artists_links"
    link = Column(String, primary_key=True, index=True)
    artist_id = Column(String, ForeignKey("artist.id"), primary_key=True, index=True)
    link_type = Column(String)
    date_added = Column(Date, default=date.today)
    artist = relationship("Artist", back_populates="links")

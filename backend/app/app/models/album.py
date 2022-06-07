from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .label import Label  # noqa: F401
    from .track import Track  # noqa: F401
    from .artist import Artist  # noqa: F401


class Album(Base):
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    total_tracks = Column(Integer)
    release_date = Column(Date(), nullable=False, index=True)
    type = Column(String)
    label_id = Column(ForeignKey("label.id"), index=True, nullable=True)
    cover = Column(String)
    label = relationship("Label", back_populates="albums")
    tracks = relationship("Track", back_populates="album")
    artists = relationship("Artist", secondary="album_artist", back_populates="albums")

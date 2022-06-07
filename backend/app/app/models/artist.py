from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .artist_stat import Artist_Stat  # noqa: F401
    from .artist_link import Artist_Link  # noqa: F401
    from .genre import Genre  # noqa: F401
    from .city_count import City_Count  # noqa: F401
    from .city import City  # noqa: F401
    from .album import Album  # noqa: F401
    from .track import Track  # noqa: F401


class Artist(Base):
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    verified = Column(Boolean())
    active = Column(Boolean())
    stats = relationship("Artist_Stat", back_populates="artist")
    links = relationship("Artist_Link", back_populates="artist")
    genres = relationship("Genre", secondary="genre_artist", back_populates="artists")
    top_cities = relationship("City_Count", back_populates="artist")
    cities = relationship("City", secondary="city_artist", back_populates="artists")
    albums = relationship("Album", secondary="album_artist", back_populates="artists")
    tracks = relationship("Track", secondary="track_artist", back_populates="artists")

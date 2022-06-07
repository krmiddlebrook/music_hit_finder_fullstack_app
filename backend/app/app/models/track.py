from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .album import Album  # noqa: F401
    from .track_playcount import Track_Playcount  # noqa: F401
    from .artist import Artist  # noqa: F401
    from .playlist import Playlist  # noqa: F401
    from .spectrogram import Spectrogram  # noqa: F401
    from .spotify_user import Spotify_User  # noqa: F401


class Track(Base):
    # __tablename__ = "tracks"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    track_number = Column(Integer)
    explicit = Column(Boolean())
    duration_ms = Column(Integer)
    isrc = Column(String, index=True)
    preview_url = Column(String)
    album_id = Column(String, ForeignKey("album.id"), index=True)
    album = relationship("Album", back_populates="tracks")
    playcounts = relationship("Track_Playcount", back_populates="track")
    artists = relationship("Artist", secondary="track_artist", back_populates="tracks")
    playlists = relationship(
        "Playlist", secondary="track_playlist", back_populates="tracks"
    )
    users = relationship(
        "Spotify_User", secondary="track_user", back_populates="tracks"
    )
    spectrogram = relationship("Spectrogram", uselist=False, back_populates="track")
    predictions = relationship("Track_Prediction", back_populates="track")

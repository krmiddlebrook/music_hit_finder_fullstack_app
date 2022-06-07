from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .user_followers_count import User_Followers_Count  # noqa: F401
    from .playlist import Playlist  # noqa: F401
    from .track import Track  # noqa: F401
    from .user import User  # noqa: F401


class Spotify_User(Base):
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    # musicai_playlist_id = Column(String, ForeignKey('musicai_playlist.playlist_id'))

    followers_counts = relationship("User_Followers_Count", back_populates="user")
    playlists = relationship("Playlist", back_populates="user")
    tracks = relationship("Track", secondary="track_user", back_populates="users")
    owner = relationship("User", back_populates="spotify", uselist=False)

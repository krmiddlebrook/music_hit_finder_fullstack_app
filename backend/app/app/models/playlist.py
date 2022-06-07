from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .spotify_user import Spotify_User  # noqa: F401
    from .playlist_followers_count import Playlist_Followers_Count  # noqa: F401
    from .search_term import Search_Term  # noqa: F401
    from .track import Track  # noqa: F401


class Playlist(Base):
    id = Column(String, primary_key=True, index=True)
    owner_id = Column(String, ForeignKey("spotify_user.id"), index=True)
    name = Column(String, index=True)

    followers_counts = relationship(
        "Playlist_Followers_Count", back_populates="playlist"
    )
    search_terms = relationship(
        "Search_Term", secondary="term_playlist", back_populates="playlists"
    )
    user = relationship("Spotify_User", back_populates="playlists")
    tracks = relationship(
        "Track", secondary="track_playlist", back_populates="playlists"
    )

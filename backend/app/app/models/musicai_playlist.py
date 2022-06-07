from typing import TYPE_CHECKING
import datetime

from sqlalchemy import Column, ForeignKey, String, Date
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .spotify_user import Spotify_User  # noqa: F401
    from .playlist import Playlist  # noqa: F401


class Musicai_Playlist(Base):
    playlist_id = Column(
        String, ForeignKey("playlist.id"), primary_key=True, index=True
    )
    owner_id = Column(String, ForeignKey("spotify_user.id"), index=True)
    playlist_url = Column(String)
    last_updated = Column(Date, index=True, onupdate=datetime.date.today)

    playlist = relationship("Playlist")
    user = relationship("Spotify_User")

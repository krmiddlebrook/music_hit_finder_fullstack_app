# from datetime import date

from sqlalchemy import Column, ForeignKey, String

from app.db.base_class import Base


class Track_Playlist(Base):
    # __tablename__ = "tracks_playlists"
    track_id = Column(String, ForeignKey("track.id"), primary_key=True, index=True)
    playlist_id = Column(
        String, ForeignKey("playlist.id"), primary_key=True, index=True
    )
    # date = Column(Date, default=date.today)

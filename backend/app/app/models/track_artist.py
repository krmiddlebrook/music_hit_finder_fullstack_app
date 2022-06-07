from sqlalchemy import Column, ForeignKey, String

from app.db.base_class import Base


class Track_Artist(Base):
    # __tablename__ = "tracks_artists"
    track_id = Column(String, ForeignKey("track.id"), primary_key=True, index=True)
    artist_id = Column(String, ForeignKey("artist.id"), primary_key=True, index=True)

from sqlalchemy import Column, ForeignKey, String

from app.db.base_class import Base


class Album_Artist(Base):
    # __tablename__ = "albums_artists"
    album_id = Column(String, ForeignKey("album.id"), primary_key=True, index=True)
    artist_id = Column(String, ForeignKey("artist.id"), primary_key=True, index=True)

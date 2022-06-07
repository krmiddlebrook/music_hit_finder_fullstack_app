from sqlalchemy import Column, ForeignKey, String

from app.db.base_class import Base


class Genre_Artist(Base):
    # __tablename__ = "genres_artists"
    genre_id = Column(String, ForeignKey("genre.id"), primary_key=True, index=True)
    artist_id = Column(String, ForeignKey("artist.id"), primary_key=True, index=True)


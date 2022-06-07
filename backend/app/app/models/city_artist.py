from sqlalchemy import Column, ForeignKey, String

from app.db.base_class import Base


class City_Artist(Base):
    # __tablename__ = "cities_artists"
    city_id = Column(String, ForeignKey("city.id"), primary_key=True, index=True)
    artist_id = Column(String, ForeignKey("artist.id"), primary_key=True, index=True)

from typing import TYPE_CHECKING
from datetime import date

from sqlalchemy import Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .city import City  # noqa: F401
    from .artist import Artist  # noqa: F401


class City_Count(Base):
    # __tablename__ = "cities_counts"
    # Id is <city_id>_<artist_id>_<date>
    id = Column(String, primary_key=True, index=True)
    city_id = Column(String, ForeignKey("city.id"), index=True)
    artist_id = Column(String, ForeignKey("artist.id"), index=True)
    date = Column(Date, default=date.today, index=True)
    listeners_count = Column(Integer, nullable=False)
    city = relationship("City", back_populates="city_counts")
    artist = relationship("Artist", back_populates="top_cities")

from typing import TYPE_CHECKING

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .city_count import City_Count  # noqa: F401
    from .artist import Artist  # noqa: F401


class City(Base):
    # __tablename__ = "cities"
    # Id is <city>:<region>:<country>
    id = Column(String, primary_key=True, index=True)
    city = Column(String, index=True, nullable=False)
    region = Column(String, index=True, nullable=False)
    country = Column(String, index=True, nullable=False)
    city_counts = relationship("City_Count", back_populates="city")
    artists = relationship("Artist", secondary="city_artist", back_populates="cities")

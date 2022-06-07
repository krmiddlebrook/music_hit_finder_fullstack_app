from typing import TYPE_CHECKING

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .album import Album  # noqa: F401


class Label(Base):
    id = Column(String, primary_key=True, index=True)
    # name = Column(String, index=True, nullable=False)
    albums = relationship("Album", back_populates="label")

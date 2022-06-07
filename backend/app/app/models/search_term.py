from typing import TYPE_CHECKING

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .playlist import Playlist  # noqa: F401


class Search_Term(Base):
    # __tablename__ = "search_terms"
    # The id is the term, e.g., id = "pop punk".
    id = Column(String, primary_key=True, index=True)
    playlists = relationship(
        "Playlist", secondary="term_playlist", back_populates="search_terms"
    )

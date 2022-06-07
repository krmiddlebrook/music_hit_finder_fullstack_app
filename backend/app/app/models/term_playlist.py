from sqlalchemy import Column, ForeignKey, String

from app.db.base_class import Base


class Term_Playlist(Base):
    # __tablename__ = "terms_playlists"
    term_id = Column(String, ForeignKey("search_term.id"), primary_key=True, index=True)
    playlist_id = Column(
        String, ForeignKey("playlist.id"), primary_key=True, index=True
    )

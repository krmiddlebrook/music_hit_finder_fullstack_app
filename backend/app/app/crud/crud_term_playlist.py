from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.term_playlist import Term_Playlist
from app.schemas.term_playlist import (
    TermPlaylistCreate,
    TermPlaylistUpdate,
)


class CRUDTermPlaylist(CRUDBase[Term_Playlist, TermPlaylistCreate, TermPlaylistUpdate]):
    def get(self, db: Session, *, term_id: str, playlist_id: str):
        return (
            db.query(Term_Playlist)
            .filter(
                Term_Playlist.term_id == term_id,
                Term_Playlist.playlist_id == playlist_id,
            )
            .first()
        )


term_playlist = CRUDTermPlaylist(Term_Playlist)

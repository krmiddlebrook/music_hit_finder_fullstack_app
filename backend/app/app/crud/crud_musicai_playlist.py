from typing import Any, Dict, Optional, Union
import datetime
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.spotify_user import Spotify_User
from app.models.musicai_playlist import Musicai_Playlist
from app.schemas.spotify_user import SpotifyUserCreate, SpotifyUserUpdate
from app.schemas.musicai_playlist import (
    MusicaiPlaylist,
    MusicaiPlaylistCreate,
    MusicaiPlaylistUpdate,
)


class CRUDMusicaiPlaylist(
    CRUDBase[Musicai_Playlist, MusicaiPlaylistCreate, MusicaiPlaylistUpdate]
):
    # TODO: add functions to get the tracks and playlists for a user
    def get(
        self, db: Session, *, playlist_id: str, spotify_user_id: str
    ) -> Optional[Musicai_Playlist]:
        return (
            db.query(Musicai_Playlist)
            .filter(
                Musicai_Playlist.playlist_id == playlist_id,
                Musicai_Playlist.owner_id == spotify_user_id,
            )
            .first()
        )

    def get_by_user(
        self, db: Session, *, spotify_user_id: str
    ) -> Optional[Musicai_Playlist]:
        return (
            db.query(Musicai_Playlist)
            .filter(Musicai_Playlist.owner_id == spotify_user_id)
            .first()
        )

    def create(self, db: Session, *, obj_in: MusicaiPlaylistCreate) -> Musicai_Playlist:
        obj_in = MusicaiPlaylist(
            playlist_id=obj_in.playlist_id,
            owner_id=obj_in.owner_id,
            playlist_url=obj_in.playlist_url,
            last_updated=datetime.date.today(),
        )
        return super().create(db, obj_in=obj_in, refresh=False)

    def update(self, db: Session, *, db_obj: Musicai_Playlist) -> Musicai_Playlist:
        db_obj.last_updated = datetime.date.today()
        db.commit()
        return db_obj


musicai_playlist = CRUDMusicaiPlaylist(Musicai_Playlist)

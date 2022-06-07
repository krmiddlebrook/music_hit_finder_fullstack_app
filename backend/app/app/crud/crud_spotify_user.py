from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.spotify_user import Spotify_User

# from app.models.musicai_playlist import Musicai_Playlist
from app.schemas.spotify_user import SpotifyUserCreate, SpotifyUserUpdate


class CRUDSpotifyUser(CRUDBase[Spotify_User, SpotifyUserCreate, SpotifyUserUpdate]):
    # TODO: add functions to get the tracks and playlists for a user
    def get_by_name(self, db: Session, *, name: str) -> Optional[Spotify_User]:
        return db.query(Spotify_User).filter(Spotify_User.name == name).first()


spotify_user = CRUDSpotifyUser(Spotify_User)

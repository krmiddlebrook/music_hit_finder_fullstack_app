from typing import Optional, List, Dict, Any

from pydantic import BaseModel
from .artist import SpotifyArtist
from .track import Track, SpotifyTrack


# Shared properties
class UserPlaylistBase(BaseModel):
    user_id: str


# Properties to receive via API on creation
class UserPlaylistCreate(UserPlaylistBase):
    artists: List[SpotifyArtist] = []
    # tracks: List[SpotifyTrack] = []
    tracks: List[Any] = []
    playlist_url: str


# Additional properties to return via API
class UserPlaylist(UserPlaylistBase):
    user_id: str
    playlist_id: str
    playlist_url: str
    tracks: List[Any]

from typing import Optional, Dict, List, Any

from pydantic import BaseModel, AnyHttpUrl


# Shared properties
class TrackBase(BaseModel):
    id: str
    name: Optional[str] = None
    track_number: Optional[int] = None
    explicit: Optional[bool] = None
    duration_ms: Optional[int] = None
    preview_url: Optional[AnyHttpUrl] = None
    isrc: Optional[str] = None
    album_id: str


# Properties to receive on item creation
class TrackCreate(TrackBase):
    album: Optional[Dict[str, Any]] = {}
    artists: Optional[List[Dict[str, Any]]] = []


# Properties to receive on item update
class TrackUpdate(TrackBase):
    pass


# Properties shared by models stored in DB
class TrackInDBBase(TrackBase):
    class Config:
        orm_mode = True


# Properties to return to client
class Track(TrackInDBBase):
    pass


# Properties stored in DB
class TrackInDB(TrackInDBBase):
    pass


# Properties to recieve via Spotify API for Track Object
class SpotifyTrack(BaseModel):
    # TODO: make objects for simplified spotify album and artist
    album: Dict[str, Any]
    artists: List[Dict[str, Any]]
    available_markets: List[str]
    disc_number: int
    duration_ms: int
    explicit: bool
    external_ids: Dict[str, Any]
    external_urls: Dict[str, Any]
    href: str
    id: str
    is_playable: Optional[bool] = None
    linked_from: Optional[Dict[str, Any]] = None
    name: str
    popularity: int
    preview_url: Optional[str] = None
    track_number: int
    type: Optional[str] = "track"
    uri: str

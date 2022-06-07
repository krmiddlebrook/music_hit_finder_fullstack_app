from typing import Optional, List, Dict, Any

from pydantic import BaseModel
from .genre import Genre
from .artist_link import ArtistLink


# Shared properties
class ArtistBase(BaseModel):
    id: str
    name: Optional[str] = None
    verified: Optional[bool] = None
    active: Optional[bool] = None
    # TODO: artist image


# Properties to receive via API on creation
class ArtistCreate(ArtistBase):
    related_artists: Optional[List[ArtistBase]] = []
    links: Optional[List[ArtistLink]] = []
    genres: Optional[List[Genre]] = []
    releases: Optional[Dict[str, Any]] = {}
    # TODO: cities, stats, playlists
    # cities: Optional[List[]]


# Properties to receive via API on update
class ArtistUpdate(ArtistBase):
    related_artists: Optional[List[ArtistBase]] = []
    links: Optional[List[ArtistLink]] = []
    genres: Optional[List[Genre]] = []
    releases: Optional[Dict[str, Any]] = {}


# Properties shared by models stored in DB
class ArtistInDBBase(ArtistBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class Artist(ArtistInDBBase):
    pass


# Additional properties stored in DB
class ArtistInDB(ArtistInDBBase):
    pass


# Properties to recieve via Spotify API for Artist Objects
class SpotifyArtist(BaseModel):
    external_urls: Dict[str, Any]
    followers: Dict[str, Any]
    genres: List[str]
    href: str
    id: str
    images: List[Dict[str, Any]]
    name: str
    popularity: int
    type: str = "artist"
    uri: str

from typing import List, Optional

from pydantic import BaseModel

from .track import Track
from .album import Album
from .artist import Artist


class TrackRisingBase(BaseModel):
    id: str
    playcount: float
    chg: float
    growth_rate: float
    period_days: int
    prediction: Optional[float] = None
    probability: Optional[float] = None
    musicai_score: Optional[int] = None


class TrackRising(TrackRisingBase):
    track: Track
    artists: List[Artist]
    album: Album
    days_since_release: Optional[int] = None

    class Config:
        orm_mode = True

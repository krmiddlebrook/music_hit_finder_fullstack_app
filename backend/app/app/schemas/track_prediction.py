from typing import Optional
from datetime import datetime

from pydantic import BaseModel


# Shared properties
class TrackPredictionBase(BaseModel):
    track_id: str
    model_id: str
    date: datetime
    prediction: float
    probability: float


# Properties to receive via API on creation
class TrackPredictionCreate(TrackPredictionBase):
    pass


# Properties to receive via API on update
class TrackPredictionUpdate(TrackPredictionBase):
    pass


# Properties shared by models stored in DB
class TrackPredictionInDBBase(TrackPredictionBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class TrackPrediction(TrackPredictionInDBBase):
    pass


# Additional properties stored in DB
class TrackPredictionInDB(TrackPredictionInDBBase):
    pass

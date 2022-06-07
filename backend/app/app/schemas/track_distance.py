from pydantic import BaseModel


# Shared properties
class TrackDistanceBase(BaseModel):
    model_id: str
    distance_type: str
    distance: float


# Properties to receive via API on creation
class TrackDistanceCreate(TrackDistanceBase):
    t1_id: str
    t2_id: str


# Properties to receive via API on update
class TrackDistanceUpdate(TrackDistanceBase):
    pass


# Properties shared by models stored in DB
class TrackDistanceInDBBase(TrackDistanceBase):
    # Id is <src_id>_<tgt_id>_<model_id>_<distance_type>
    # Note: src_id < tgt_id
    id: str
    src_id: str
    tgt_id: str

    class Config:
        orm_mode = True


# Additional properties to return via API
class TrackDistance(TrackDistanceInDBBase):
    pass


# Additional properties stored in DB
class TrackDistanceInDB(TrackDistanceInDBBase):
    pass

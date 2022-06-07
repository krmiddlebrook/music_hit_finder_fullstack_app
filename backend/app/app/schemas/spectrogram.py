from typing import Optional
from pydantic import BaseModel


# Shared properties
class SpectrogramBase(BaseModel):
    track_id: str
    spectrogram_type: str
    hop_size: int
    window_size: int
    n_mels: int
    is_corrupt: Optional[bool] = False
    spectrogram: Optional[bytes] = None


# Properties to receive via API on creation
class SpectrogramCreate(SpectrogramBase):
    pass


# Properties to receive via API on update
class SpectrogramUpdate(SpectrogramBase):
    pass


# Properties shared by models stored in DB
class SpectrogramInDBBase(SpectrogramBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class Spectrogram(SpectrogramInDBBase):
    pass


# Additional properties stored in DB
class SpectrogramInDB(SpectrogramInDBBase):
    pass

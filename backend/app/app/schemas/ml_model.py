from typing import Optional
from datetime import datetime

from pydantic import BaseModel


# Shared properties
class MLModelBase(BaseModel):
    id: str
    model_type: str
    date_trained: datetime
    epochs: int
    extra_metadata: Optional[str] = None


# Properties to receive via API on creation
class MLModelCreate(MLModelBase):
    pass


# Properties to receive via API on update
class MLModelUpdate(MLModelBase):
    pass


# Properties shared by models stored in DB
class MLModelInDBBase(MLModelBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class MLModel(MLModelInDBBase):
    pass


# Additional properties stored in DB
class MLModelInDB(MLModelInDBBase):
    pass

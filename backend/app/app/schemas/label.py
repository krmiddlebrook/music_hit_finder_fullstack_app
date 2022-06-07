# from typing import Optional
from pydantic import BaseModel


# Shared properties
class LabelBase(BaseModel):
    id: str


# Properties to receive via API on creation
class LabelCreate(LabelBase):
    pass


# Properties to receive via API on update
class LabelUpdate(LabelBase):
    pass


# Properties shared by models stored in DB
class LabelInDBBase(LabelBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class Label(LabelInDBBase):
    pass


# Additional properties stored in DB
class LabelInDB(LabelInDBBase):
    pass

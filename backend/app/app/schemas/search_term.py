from pydantic import BaseModel


# Shared properties
class SearchTermBase(BaseModel):
    id: str  # The search term eg, "pop punk"


# Properties to receive on item creation
class SearchTermCreate(SearchTermBase):
    pass


# Properties to receive on item update
class SearchTermUpdate(SearchTermBase):
    pass


# Properties shared by models stored in DB
class SearchTermInDBBase(SearchTermBase):
    class Config:
        orm_mode = True


# Properties to return to client
class SearchTerm(SearchTermInDBBase):
    pass


# Properties stored in DB
class SearchTermInDB(SearchTermInDBBase):
    pass

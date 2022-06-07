from app.crud.base import CRUDBase
from app.models.search_term import Search_Term
from app.schemas.search_term import SearchTermCreate, SearchTermUpdate


class CRUDSearchTerm(CRUDBase[Search_Term, SearchTermCreate, SearchTermUpdate]):
    pass


search_term = CRUDSearchTerm(Search_Term)

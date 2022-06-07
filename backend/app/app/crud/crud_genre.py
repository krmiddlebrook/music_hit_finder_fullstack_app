# from typing import Any, Dict, Optional, Union

# from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.genre import Genre
from app.schemas.genre import GenreCreate, GenreUpdate


class CRUDGenre(CRUDBase[Genre, GenreCreate, GenreUpdate]):
    pass


genre = CRUDGenre(Genre)

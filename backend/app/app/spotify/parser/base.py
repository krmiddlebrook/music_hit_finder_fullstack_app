from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

# from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

# from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)


class ParseBase(Generic[ModelType, CreateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        Parse object with default methods to build the object.

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def uri2id(self, uri: str) -> Optional[str]:
        """
        Extract item id from spotify uri.

        Ex:
        uri = "spotify:`item_type`:2GHclqNVjqGuiE5mA7BEoc"
        return "2GHclqNVjqGuiE5mA7BEoc"

        `item_type` can be artist, track, album, user, playlist
        """
        uri = uri.split(":")
        if len(uri) != 3:
            return None
        return uri[-1]


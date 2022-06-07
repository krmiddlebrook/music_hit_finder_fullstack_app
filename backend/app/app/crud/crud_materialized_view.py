from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text, Integer, String, Float, Boolean, BigInteger
from sqlalchemy import bindparam
from sqlalchemy.exc import IntegrityError
from celery.utils.log import get_task_logger

from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


logger = get_task_logger(__name__)


class CRUDMaterializedView(object):
    def __init__(self):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        # self.model = model
        pass

    def get_names(self, db: Session) -> List[str]:
        """
        Retrieve a list of names of materialized view that exist in the db
        """
        stmt = """
            select
                relname "name"
            from pg_class
            where relkind = 'm';
        """
        stmt = text(stmt).columns(name=String)
        names = [mv.name for mv in db.execute(stmt).fetchall()]
        return names

    def refresh_view(self, db: Session, mv_name: str) -> str:
        """
        Refresh the materialized view specified by mv_name.

        Returns:
            The mv_name parameter.
        """
        stmt = f"""
            REFRESH MATERIALIZED VIEW {mv_name};
        """
        db.execute(text(stmt))
        db.commit()
        return mv_name

    def refresh_all(self, db: Session) -> List[str]:
        """
        Refresh all existing materialized views in the db.

        Returns:
            A list of names of the materialized view that were refreshed.
        """
        names = self.get_names(db)
        for mv in names:
            stmt = f"""
                REFRESH MATERIALIZED VIEW {mv};
            """
            db.execute(text(stmt))
            db.commit()
        return names

    # def get_with_cache(self, db: Session, compiled_cache: Dict):
    #      """reusing the same statement + compiled cache."""

    #     compiled_cache = {}
    #     stmt = select([Customer.__table__]).where(Customer.id == bindparam("id"))
    #     with db.connect().execution_options(
    #         compiled_cache=compiled_cache
    #     ) as conn:
    #         for id_ in random.sample(ids, n):
    #             row = conn.execute(stmt, id=id_).first()
    #             tuple(row)


materialized_view = CRUDMaterializedView()

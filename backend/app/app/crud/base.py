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


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

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

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: Optional[int] = 100
    ) -> List[ModelType]:
        if limit:
            return db.query(self.model).offset(skip).limit(limit).all()
        else:
            return db.query(self.model).offset(skip).all()

    def get_multi_by_ids(self, db: Session, *, ids: List[str]) -> List[ModelType]:
        """
        Retrieve a list of db objects in the db given a set of ids.
        """
        return db.query(self.model).filter(self.model.id.in_(ids)).all()

    def get_missing_ids_by_ids(self, db: Session, *, ids: List[str]) -> List[Any]:
        """
        Retrieve the ids in the passed ids list that do not exist in the db.
        """
        db_obj_ids = set(
            [
                db_obj.id
                for db_obj in db.query(self.model.id)
                .filter(self.model.id.in_(ids))
                .all()
            ]
        )
        ids = set(ids)
        missing_ids = ids.difference(db_obj_ids)
        return list(missing_ids)

    def create(
        self, db: Session, *, obj_in: CreateSchemaType, refresh: bool = True
    ) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        try:
            # Add the db_obj to the db
            db.add(db_obj)
            db.commit()
            if refresh:
                db.refresh(db_obj)
        except IntegrityError as integ_err:  # noqa: F841
            logger.warning(
                f"Unique constraint violated for {self.model.__tablename__} \n"
                f" {integ_err} \n "
            )
            logger.warning(f"Object in: {obj_in}")
            db.rollback()
        except Exception as err:  # noqa: F841
            logger.warning(f"ERROR Inserting to {self.model.__tablename__} \n {err} \n")
            logger.warning(f"Object in: {obj_in}")
            db.rollback()
        return db_obj

    def create_multi(
        self, db: Session, *, objs_in: List[Union[CreateSchemaType, Dict[str, Any]]],
    ) -> bool:
        """
        A convenience function to safely bulk insert a list of objects into the
        appropriate database table efficiently. When applied correctly, this
        function bypasses SQLAlchemy's unit-of-work operations reducing a
        significant amount of python overhead and resulting in a non-trivial
        performance improvement because inserts and updates can be optimized
        according to the dbapi's executemany() process. Note: primary key must
        be supplied by the incoming objects.

        More details here:
            https://docs.sqlalchemy.org/en/14/core/tutorial.html#execute-multiple
        """
        if len(objs_in) == 0:
            # Do nothing if there are no entries in the objs_in list/dict.
            return True
        if not isinstance(objs_in[0], dict):
            # Convert the list of CreateSchemaType to dict b/c that's the format sql
            # expects.
            objs_in = [jsonable_encoder(obj) for obj in objs_in]
        success = False
        try:
            # Push objs_in to the given table.
            # At this point objs_in should be a list of dicts.
            db.execute(self.model.__table__.insert(), objs_in)
            db.commit()
            success = True
        except IntegrityError as integ_err:  # noqa: F841
            logger.warning(f"Unique constraint violated for {self.model.__tablename__}")
            logger.warning(integ_err)
            db.rollback()
        except Exception as err:  # noqa: F841
            logger.warning(f"ERROR Inserting to {self.model.__tablename__} \n {err}")
            db.rollback()
        return success

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        refresh: bool = True,
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        if refresh:
            db.refresh(db_obj)
        return db_obj

    def update_multi(
        self, db: Session, *, objs_in: List[Union[UpdateSchemaType, Dict[str, Any]]],
    ) -> bool:
        """
        A convenience function to safely bulk update a list of objects into the
        appropriate database table efficiently. When applied correctly, this
        function bypasses SQLAlchemy's unit-of-work operations reducing a
        significant amount of python overhead and resulting in a non-trivial
        performance improvement because inserts and updates can be optimized
        according to the dbapi's executemany() process. Note: primary key must
        be supplied by the incoming objects and each object must contain the
        same set of parameters. WARNING: don't use this operation if you aren't
        familier with SQLAlchemy and more generally SQL, instead use the update
        funtion to update above applied to each object.

        More details here:
            https://docs.sqlalchemy.org/en/14/core/tutorial.html#execute-multiple
        """
        if len(objs_in) == 0:
            # Do nothing if there are no entries in the objs_in list/dict.
            return True
        if not isinstance(objs_in[0], dict):
            # Convert the list of CreateSchemaType to dict b/c that's the format sql
            # expects.
            objs_in = [jsonable_encoder(obj) for obj in objs_in]

        formated_objs_in = []
        for obj in objs_in:
            obj["_id"] = obj.pop("id")
            formated_objs_in.append(obj)

        # TODO: experiment with retrieving the associated db objects first, looping
        # through each object, and applying the incoming update params (objs_in) them.
        success = False
        try:
            # Push objs_in to the given table.
            # At this point objs_in should be a list of dicts.
            db.execute(
                self.model.__table__.update().where(
                    self.model.__table__.c.id == bindparam("_id")
                ),
                formated_objs_in,
            )
            db.commit()
            success = True
        except IntegrityError as integ_err:  # noqa: F841
            logger.warning(f"Unique constraint violated for {self.model.__tablename__}")
            logger.warning(integ_err)
            db.rollback()
        except Exception as err:  # noqa: F841
            logger.warning(f"ERROR Inserting to {self.model.__tablename__} \n {err}")
            db.rollback()
        return success

    def remove(self, db: Session, *, id: int) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj

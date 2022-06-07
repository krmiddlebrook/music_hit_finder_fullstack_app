from typing import Optional, List

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.ml_model import ML_Model
from app.schemas.ml_model import MLModelCreate, MLModelUpdate


class CRUDMLModel(CRUDBase[ML_Model, MLModelCreate, MLModelUpdate]):
    def get_by_model_type(
        self, db: Session, *, model_type: str
    ) -> Optional[List[ML_Model]]:
        return db.query(ML_Model).filter(ML_Model.model_type == model_type).all()

    pass


ml_model = CRUDMLModel(ML_Model)

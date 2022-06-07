from typing import Optional

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.label import Label
from app.schemas.label import LabelCreate, LabelUpdate


class CRUDLabel(CRUDBase[Label, LabelCreate, LabelUpdate]):
    pass
    # def get_by_name(self, db: Session, name: str) -> Optional[Label]:
    #     return db.query(Label).filter(Label.name == name).first()


label = CRUDLabel(Label)

from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer

from app.db.base_class import Base


class ML_Model(Base):
    # id = <model_type>_<date_trained>_<epochs>_<extra_metadata>
    id = Column(String, primary_key=True, index=True)
    model_type = Column(String, index=True, nullable=False)
    date_trained = Column(DateTime, index=True, nullable=False, default=datetime.now)
    epochs = Column(Integer, index=True, nullable=False)
    extra_metadata = Column(String)

from sqlalchemy import Column, ForeignKey, String, Float

from app.db.base_class import Base


class Track_Distance(Base):
    # Id is <src_id>_<tgt_id>_<model_id>_<distance_type>
    # Note: <src_id> < <tgt_id>
    # e.g., Given track1_id='p', track2_id='c',
    # id = c_p_<model_id>_<distance_type>
    id = Column(String, primary_key=True, index=True)
    src_id = Column(String, ForeignKey("track.id"), index=True, nullable=False)
    tgt_id = Column(String, ForeignKey("track.id"), index=True, nullable=False)
    model_id = Column(String, ForeignKey("ml_model.id"), index=True, nullable=False)
    distance_type = Column(String, index=True, nullable=False)
    distance = Column(Float, nullable=False)

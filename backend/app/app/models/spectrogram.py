from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, Boolean, LargeBinary, Integer
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .track import Track  # noqa: F401


class Spectrogram(Base):
    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(String, ForeignKey("track.id"), index=True)
    spectrogram_type = Column(String, index=True, nullable=False)
    hop_size = Column(Integer, index=True, nullable=False)
    window_size = Column(Integer, index=True, nullable=False)
    n_mels = Column(Integer, index=True, nullable=False)
    is_corrupt = Column(Boolean, default=False, nullable=False)
    spectrogram = Column(LargeBinary)
    track = relationship("Track", back_populates="spectrogram", uselist=False)

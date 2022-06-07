from typing import Optional, List, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from celery.utils.log import get_task_logger

from app.crud.base import CRUDBase
from app.models.spectrogram import Spectrogram
from app.schemas.spectrogram import SpectrogramCreate, SpectrogramUpdate
from app.core.config import settings

logger = get_task_logger(__name__)


class CRUDSpectrogram(CRUDBase[Spectrogram, SpectrogramCreate, SpectrogramUpdate]):
    def create(self, db: Session, *, obj_in: SpectrogramCreate,) -> Spectrogram:
        spec = Spectrogram(
            track_id=obj_in.track_id,
            spectrogram_type=obj_in.spectrogram_type,
            hop_size=obj_in.hop_size,
            window_size=obj_in.window_size,
            n_mels=obj_in.n_mels,
            is_corrupt=obj_in.is_corrupt,
            spectrogram=obj_in.spectrogram,
        )
        # Push spectrogram to the spectrograms table.
        try:
            db.add(spec)
            db.commit()
            db.refresh(spec)
        except IntegrityError as integ_err:  # noqa: F841
            logger.warning(
                f"Unique constraint violated for {Spectrogram.__tablename__} \n {integ_err}"
            )
            db.rollback()
        except Exception as err:  # noqa: F841
            logger.warning(f"ERROR Inserting to {Spectrogram.__tablename__} \n {err}")
            db.rollback()
        finally:
            return spec

    def update_is_corrupt(
        self, db: Session, *, db_obj: Spectrogram, is_corrupt: bool
    ) -> Spectrogram:
        db_obj.is_corrupt = is_corrupt
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        *,
        track_id: str,
        spec_type: Optional[str] = settings.SPECTROGRAM_TYPE,
        hop_size: Optional[int] = settings.HOP_SIZE,
        window_size: Optional[int] = settings.WINDOW_SIZE,
        n_mels: Optional[int] = settings.N_MELS,
        simplified: Optional[bool] = False,
    ) -> Optional[Spectrogram]:
        query = (
            db.query(Spectrogram.id, Spectrogram.is_corrupt)
            if simplified
            else db.query(Spectrogram)
        )
        return query.filter(
            Spectrogram.track_id == track_id,
            Spectrogram.spectrogram_type == spec_type,
            Spectrogram.hop_size == hop_size,
            Spectrogram.window_size == window_size,
            Spectrogram.n_mels == n_mels,
        ).first()

    def get_by_track_id(self, db: Session, *, track_id: str) -> List[Spectrogram]:
        return db.query(Spectrogram).filter(Spectrogram.track_id == track_id).all()

    def get_by_track_ids(
        self,
        db: Session,
        *,
        track_ids: List[str],
        spec_type: Optional[str] = settings.SPECTROGRAM_TYPE,
        hop_size: Optional[int] = settings.HOP_SIZE,
        window_size: Optional[int] = settings.WINDOW_SIZE,
        n_mels: Optional[int] = settings.N_MELS,
    ) -> List[Spectrogram]:
        """
        Retrieve spectrograms associated with the given set of track ids.
        """
        return (
            db.query(Spectrogram)
            .filter(
                Spectrogram.track_id.in_(track_ids),
                Spectrogram.spectrogram_type == spec_type,
                Spectrogram.hop_size == hop_size,
                Spectrogram.window_size == window_size,
                Spectrogram.n_mels == n_mels,
                Spectrogram.is_corrupt == False,
            )
            .order_by(Spectrogram.track_id)
            .all()
        )

    def get_by_track_ids_simplified(
        self,
        db: Session,
        *,
        track_ids: List[str],
        spec_type: Optional[str] = settings.SPECTROGRAM_TYPE,
        hop_size: Optional[int] = settings.HOP_SIZE,
        window_size: Optional[int] = settings.WINDOW_SIZE,
        n_mels: Optional[int] = settings.N_MELS,
    ) -> List[Spectrogram]:
        """
        Retrieve track ids that have a spectrogram stored in the db.
        """
        return (
            db.query(Spectrogram.id)
            .filter(
                Spectrogram.track_id.in_(track_ids),
                Spectrogram.spectrogram_type == spec_type,
                Spectrogram.hop_size == hop_size,
                Spectrogram.window_size == window_size,
                Spectrogram.n_mels == n_mels,
                Spectrogram.is_corrupt == False,
            )
            .order_by(Spectrogram.track_id)
            .all()
        )

    def get_valid_track_ids(
        self,
        db: Session,
        *,
        track_ids: List[str],
        allow_corrupt: Optional[bool] = False,
        spec_type: Optional[str] = settings.SPECTROGRAM_TYPE,
        hop_size: Optional[int] = settings.HOP_SIZE,
        window_size: Optional[int] = settings.WINDOW_SIZE,
        n_mels: Optional[int] = settings.N_MELS,
    ) -> Optional[List[Any]]:
        """
        Retrieve tracks ids that have spectrograms in the db.
        """
        return (
            db.query(Spectrogram.track_id)
            .filter(
                Spectrogram.track_id.in_(track_ids),
                Spectrogram.is_corrupt == allow_corrupt,
                Spectrogram.spectrogram_type == spec_type,
                Spectrogram.hop_size == hop_size,
                Spectrogram.window_size == window_size,
                Spectrogram.n_mels == n_mels,
            )
            .all()
        )


spectrogram = CRUDSpectrogram(Spectrogram)

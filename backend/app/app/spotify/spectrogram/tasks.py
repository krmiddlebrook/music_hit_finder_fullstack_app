from typing import List, Optional, Dict, Any, Union, Tuple
from pathlib import Path

from celery import group, chord
from celery.utils.log import get_task_logger
from celery.result import AsyncResult
from datetime import date, timedelta

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import session_scope

from app import crud, schemas
from app.spotify import parser


logger = get_task_logger(__name__)


@celery_app.task(bind=True, task_time_limit=60, ignore_result=False, serializer="json")
def download_wav(self, track_id: str, preview_url: str) -> Optional[str]:
    wav_path = parser.spectrogram.download_wav(
        track_id, preview_url, mp3_path=settings.MP3_DIR, wav_path=settings.WAV_DIR
    )
    return str(wav_path)


@celery_app.task(bind=True, task_time_limit=6, serializer="json", queue="spec")
def push_spectrogram(
    self,
    wav_path: str,
    spectrogram_type: str = settings.SPECTROGRAM_TYPE,
    hop_size: Optional[int] = settings.HOP_SIZE,
    window_size: Optional[int] = settings.WINDOW_SIZE,
    n_mels: Optional[int] = settings.N_MELS,
) -> Dict[str, Any]:
    with session_scope() as db:
        wav_path = Path(wav_path)
        spec = parser.spectrogram.wav2spec(
            wav_path,
            spectrogram_type=spectrogram_type,
            hop_size=hop_size,
            window_size=window_size,
            n_mels=n_mels,
            delete_wav=True,
        )
        if spec:
            spec = crud.spectrogram.create(db, obj_in=spec)
            return {"track_id": spec.track_id, "is_corrupt": spec.is_corrupt}
        else:
            return {"track_id": wav_path.stem, "is_corrupt": True}


@celery_app.task(bind=True, ignore_result=True, serializer="json")
def flow_spectrogram(
    self,
    track_id: str,
    preview_url: str,
    spectrogram_type: Optional[str] = settings.SPECTROGRAM_TYPE,
    hop_size: int = settings.HOP_SIZE,
    window_size: int = settings.WINDOW_SIZE,
    n_mels: int = settings.N_MELS,
    check_db_first: Optional[bool] = False,
) -> None:
    """
    Downloads spotify preview audio, coverts it to a spectrogram, and pushes it to
    the db.
    """
    if check_db_first:
        with session_scope() as db:
            db_spec = crud.spectrogram.get(
                db,
                track_id=track_id,
                spec_type=spectrogram_type,
                hop_size=hop_size,
                window_size=window_size,
                n_mels=n_mels,
                simplified=True,
            )
            if db_spec:
                if not db_spec.is_corrupt:
                    # Spectrogram already in db
                    return

    workflow = download_wav.si(
        track_id=track_id, preview_url=preview_url
    ) | push_spectrogram.s(
        spectrogram_type=spectrogram_type,
        hop_size=hop_size,
        window_size=window_size,
        n_mels=n_mels,
    )
    workflow.apply_async()
    # return workflow()


# TODO: Write get spectrograms by track id function

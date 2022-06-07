from typing import List, Optional, Dict, Any, Union, Tuple
from pathlib import Path

from celery import group, chord
from celery.utils.log import get_task_logger
from datetime import date, timedelta

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import session_scope

from app import crud, schemas
from app.spotify import parser


logger = get_task_logger(__name__)


@celery_app.task(bind=True)
def flow_scrape_spectrograms(
    self,
    min_date: date = date.today() - timedelta(days=365),
    max_date: date = date.today(),
    skip: Optional[int] = 0,
    limit: Optional[int] = 5_000,
) -> None:
    """
    Collect spectrograms for tracks.

    The flow performs the following steps:
        get track ids (only include rising tracks by verified artists and with preview_urls)
        for each track:
            chain(
                download spectrogram (if necessary),
                push spectrogram
            )
                
    repeat: 2/week
    """
    with session_scope() as db:
        # tracks = crud.track.get_tracks_missing_spectrograms(db, skip=0, limit=100)
        # TODO: filter to include rising tracks by verified artists and with preview_url
        tracks = [
            (t.id, t.preview_url)
            for t in crud.track.get_tracks_missing_spectrograms(
                db, skip=skip, limit=limit
            )
        ]

    logger.info(f"Collecting spectrograms for {len(tracks)} tracks.")

    for tid, t_preview_url in tracks:
        push_spectrogram.si(
            tid,
            t_preview_url,
            settings.SPECTROGRAM_TYPE,
            settings.HOP_SIZE,
            settings.WINDOW_SIZE,
            settings.N_MELS,
        ).apply_async()

    # logger.info(f"SPECTROGRAMS TASKS called for ({len(track_ids)}) tracks.")


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def download_wav(self, track_id: str, preview_url: str) -> Optional[Path]:
    wav_path = parser.spectrogram.download_wav(
        track_id, preview_url, mp3_path=settings.MP3_DIR, wav_path=settings.WAV_DIR
    )
    # TODO: make push_spectrogram: download_wav (if necessary) -> push_spectrogram (if download_wav successful)
    return wav_path


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_spectrogram(
    self,
    track_id: str,
    preview_url: str,
    spectrogram_type: str = settings.SPECTROGRAM_TYPE,
    hop_size: int = settings.HOP_SIZE,
    window_size: int = settings.WINDOW_SIZE,
    n_mels: int = settings.N_MELS,
) -> Optional[Tuple[str, bool]]:
    with session_scope() as db:
        spec = crud.spectrogram.get_by_track_id_and_spec_config(
            db,
            track_id=track_id,
            spectrogram_type=spectrogram_type,
            hop_size=hop_size,
            window_size=window_size,
            n_mels=n_mels,
        )
        if not spec:
            wav_path = parser.spectrogram.download_wav(
                track_id,
                preview_url,
                mp3_path=settings.MP3_DIR,
                wav_path=settings.WAV_DIR,
            )
            if wav_path:
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
        elif spec.is_corrupt:
            wav_path = parser.spectrogram.download_wav(
                track_id,
                preview_url,
                mp3_path=settings.MP3_DIR,
                wav_path=settings.WAV_DIR,
            )
            if wav_path:
                updated_spec = parser.spectrogram.wav2spec(
                    wav_path,
                    spectrogram_type=spectrogram_type,
                    hop_size=hop_size,
                    window_size=window_size,
                    n_mels=n_mels,
                    delete_wav=True,
                )
                if updated_spec:
                    if not updated_spec.is_corrupt:
                        spec.spectrogram = updated_spec.spectrogram
                        spec.is_corrupt = updated_spec.is_corrupt
                        db.commit()

        if spec:
            return spec.track_id, spec.is_corrupt
        else:
            logger.warning(f"Failed to push spectrogram for track {track_id}")

    # TODO: add function to push/update album label and make it a group with
    # push_tracks_playcounts
    # flow = download_wav.si(album_id) | push_tracks_playcounts.s()
    # flow.apply_async()


# TODO: Write get spectrograms by track id function

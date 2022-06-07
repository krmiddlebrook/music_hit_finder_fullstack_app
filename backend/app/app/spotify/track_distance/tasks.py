from typing import List, Optional, Dict, Any, Union
from collections import OrderedDict
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from celery import chord, group
from celery.utils.log import get_task_logger
import numpy as np

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import session_scope

from app import crud, schemas, models
from app.spotify import parser
from app.ml import spec_model

logger = get_task_logger(__name__)


@celery_app.task(bind=True, serializer="json", queue="distance-queue")
def flow_tracks_distances(
    self,
    track_ids: Union[List[str], str, List[Dict[str, Any]]],
    distance_type: Optional[str] = settings.DISTANCE_TYPE,
    spec_type: Optional[str] = settings.SPECTROGRAM_TYPE,
    hop_size: str = settings.HOP_SIZE,
    window_size: str = settings.WINDOW_SIZE,
    n_mels: str = settings.N_MELS,
) -> List[Dict[str, Any]]:
    """
    Calculate the distance between track embedding features for a list of track ids
    and push results to the db.

    Returns:
        A list of json encoded (dict) track distance pairs.
    """
    track_ids_are_paired = False
    if isinstance(track_ids, str):
        track_ids = track_ids.split(",")
        flat_track_ids = set(track_ids)
    elif isinstance(track_ids, list):
        if isinstance(track_ids[0], dict):
            flat_track_ids = []
            for pair in track_ids:
                flat_track_ids.append(pair["src_id"])
                flat_track_ids.append(pair["tgt_id"])
            flat_track_ids = set(flat_track_ids)
            track_ids_are_paired = True
        else:
            flat_track_ids = set(track_ids)

    with session_scope() as db:
        # Grab spectrograms for the track_ids
        db_specs = crud.spectrogram.get_by_track_ids(
            db,
            track_ids=flat_track_ids,
            spec_type=spec_type,
            hop_size=hop_size,
            window_size=window_size,
            n_mels=n_mels,
        )

        spec_dict = OrderedDict()
        for spec in db_specs:
            spec_np = parser.spectrogram.spec2numpy(spec.track_id, spec.spectrogram)
            if spec_np is not None:
                spec_dict[spec.track_id] = spec_np
            else:
                logger.warning(f"Spectrogram is corrupt! ({spec.track_id})")
                crud.spectrogram.update_is_corrupt(db, db_obj=spec, is_corrupt=True)
        spec_batch = np.array([spec for tid, spec in spec_dict.items()])

        # Get the embeddings for each track
        emb_batch = spec_model.get_features(spec_batch)
        emb_dict = OrderedDict()
        for tid, emb in zip(spec_dict.keys(), emb_batch):
            emb_dict[tid] = emb

        # Create track id pairs if needed
        if not track_ids_are_paired:
            pass

        # Calculate track distances.
        # TODO: efficiently compute distances between pairs using matrix multiplication
        # tricks
        distances = []
        for pair in track_ids:
            src_id = pair["src_id"]
            tgt_id = pair["tgt_id"]
            if src_id != tgt_id:
                pair_dist = spec_model.calculate_distance(
                    emb_dict[src_id], emb_dict[tgt_id], distance_type=distance_type,
                ).item()
                obj_pair_dist = schemas.TrackDistanceCreate(
                    t1_id=src_id,
                    t2_id=tgt_id,
                    model_id=settings.MODEL_ID,
                    distance_type=distance_type,
                    distance=pair_dist,
                )
                # Push distances to the tracks_distances table.
                # TODO: push to db using an async celery task
                # push_track_distance.si(
                #     track_distance=jsonable_encoder(obj_pair_dist)
                # ).apply_async(ignore_result=True)
                db_pair_dist = crud.track_distance.create(db, obj_in=obj_pair_dist)
                distances.append(jsonable_encoder(db_pair_dist))
        return distances


@celery_app.task(
    bind=True, task_time_limit=1, serializer="json", queue="short-queue",
)
def push_track_distance(self, track_distance: Dict[str, Any],) -> Dict[str, Any]:
    track_distance = schemas.TrackDistanceCreate(**track_distance)
    with session_scope() as db:
        db_obj = crud.track_distance.create(db, obj_in=track_distance)
        return jsonable_encoder(db_obj)

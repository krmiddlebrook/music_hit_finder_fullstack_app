from typing import List, Optional, Dict, Any, Union
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
from app.spotify.utils import chunkify


logger = get_task_logger(__name__)


@celery_app.task(bind=True, task_time_limit=30, serializer="json")
def predict_tracks(
    self,
    track_ids: Union[List[str], str],
    model_id: str = settings.MODEL_ID,
    spec_type: str = settings.SPECTROGRAM_TYPE,
    hop_size: str = settings.HOP_SIZE,
    window_size: str = settings.WINDOW_SIZE,
    n_mels: str = settings.N_MELS,
) -> List[Dict[str, Any]]:
    """
    Calculate the hit probability for the given track_id and push results to
    the db.

    Returns:
        A list of json encoded (dict) track predictions.
    """
    if isinstance(track_ids, str):
        track_ids = track_ids.split(",")

    # Grab spectrograms for the track_ids
    with session_scope() as db:
        if not crud.ml_model.get(db, id=model_id):
            model_config = model_id.split("_")
            model_type = model_config[0]
            date_trained = datetime.fromisoformat(model_config[1])
            epochs = int(model_config[2])
            extra_metadata = model_config[-1] if len(model_config) > 3 else None
            crud.ml_model.create(
                db,
                obj_in=schemas.MLModel(
                    id=model_id,
                    model_type=model_type,
                    date_trained=date_trained,
                    epochs=epochs,
                    extra_metadata=extra_metadata,
                ),
            )

        db_specs = crud.spectrogram.get_by_track_ids(
            db,
            track_ids=track_ids,
            spec_type=spec_type,
            hop_size=hop_size,
            window_size=window_size,
            n_mels=n_mels,
        )

        # format the data for the model
        track_ids, spectrograms = [], []
        for spec in db_specs:
            spec_np = parser.spectrogram.spec2numpy(spec.track_id, spec.spectrogram)
            if spec_np is not None:
                spectrograms.append(spec_np)
                track_ids.append(spec.track_id)
            else:
                logger.warning(f"Spectrogram is corrupt! ({spec.track_id})")
                crud.spectrogram.update_is_corrupt(db, db_obj=spec, is_corrupt=True)
        spectrograms = np.array(spectrograms)

    # Make hit predictions
    track_preds = []
    probs = (
        spec_model.get_predictions(spectrograms)
        .view(-1)
        .detach()
        .cpu()
        .numpy()
        .tolist()
    )
    for tid, prob in zip(track_ids, probs):
        pred = 0.0 if prob < 0.5 else 1.0
        # TODO: update this to bulk insert/update track predictions
        track_pred = schemas.TrackPrediction(
            track_id=tid,
            model_id=spec_model.model_id,
            date=datetime.now(),
            prediction=pred,
            probability=prob,
        )
        push_track_prediction.si(
            track_prediction=jsonable_encoder(track_pred)
        ).apply_async(ignore_result=True)
        track_preds.append(jsonable_encoder(track_pred))
    return track_preds


@celery_app.task(
    bind=True, task_time_limit=6, serializer="json", queue="short-queue",
)
def push_track_prediction(self, track_prediction: Dict[str, Any],) -> Dict[str, Any]:
    track_prediction = schemas.TrackPrediction(**track_prediction)
    with session_scope() as db:
        db_obj = crud.track_prediction.get(
            db, track_id=track_prediction.track_id, model_id=track_prediction.model_id
        )
        if not db_obj:
            db_obj = crud.track_prediction.create(db, obj_in=track_prediction)

        if db_obj.prediction != track_prediction.prediction:
            db_obj = crud.track_prediction.update(
                db, db_obj=db_obj, obj_in=track_prediction
            )

    return jsonable_encoder(track_prediction)

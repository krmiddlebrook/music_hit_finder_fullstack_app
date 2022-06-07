from typing import Dict, Any, List

from fastapi.encoders import jsonable_encoder
from celery import chord, group
from celery.utils.log import get_task_logger
from celery.result import AsyncResult

from app.core.celery_app import celery_app
from app.db.session import session_scope

from app import crud, schemas
from app.spotify import parser
from app.spotify.spapi import spapi
from app.spotify import track, album

logger = get_task_logger(__name__)


@celery_app.task(bind=True, task_time_limit=10, ignore_result=False, serializer="json")
def fetch_album_playcount(self, album_id: str):
    return spapi.album_playcount(album_id)


@celery_app.task(bind=True, serializer="json")
def push_album_playcount(self, album_playcount: Dict[str, Any]) -> List[Dict[str, Any]]:
    # tracks = parser.track.from_album_playcount(obj_in=album_playcount)
    playcounts = parser.track_playcount.from_album(obj_in=album_playcount)
    if not playcounts:
        logger.warning("Album Playcount is None!")
        return

    # Pushing to db here instead of in another task reduces celery load
    # at the cost of a slightly longer running task.
    # db_playcounts = []
    track_ids = [p.track_id for p in playcounts]
    date = playcounts[0].date
    with session_scope() as db:
        db_pcnt_track_ids = set(
            [
                db_obj.track_id
                for db_obj in crud.track_playcount.get_by_track_ids_and_date(
                    db, track_ids=track_ids, date=date
                )
            ]
        )
        missing_playcounts = [
            jsonable_encoder(pcnt_obj)
            for pcnt_obj in playcounts
            if pcnt_obj.track_id not in db_pcnt_track_ids
        ]
        # Bulk insert missing playcounts to db
        _ = crud.track_playcount.create_multi(db, objs_in=missing_playcounts)
        return missing_playcounts


@celery_app.task(
    bind=True, serializer="json", queue="short-queue",
)
def push_track_playcount(self, track_playcount: Dict[str, Any]) -> Dict[str, Any]:
    with session_scope() as db:
        tp_obj = schemas.TrackPlaycount(**track_playcount)
        # if not crud.track_playcount.get(db, id=tp_obj.id):
        db_tp = crud.track_playcount.create(db, obj_in=tp_obj)
        return jsonable_encoder(db_tp)


# @celery_app.task(bind=True, serializer="json")
def flow_album_playcount(album_id: str) -> Any:
    workflow = fetch_album_playcount.si(album_id) | push_album_playcount.s()
    workflow.apply_async(ignore_result=True)

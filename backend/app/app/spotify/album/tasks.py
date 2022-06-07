from typing import Dict, Any, Optional
import datetime
import time

from celery.utils.log import get_task_logger
from celery import group
from celery.result import AsyncResult
from fastapi.encoders import jsonable_encoder

from app.core.celery_app import celery_app
from app.db.session import session_scope

from app import crud
from app.spotify import parser
from app.spotify import association
from app.spotify import track_playcount
from app.spotify import artist

# from app.spotify import parser
from app.spotify.spapi import spapi
from app.spotify.spotify_mux import spotify_mux


logger = get_task_logger(__name__)


@celery_app.task(bind=True, ignore_result=False, serializer="json")
def fetch_album_data(self, album_id: str) -> Dict[str, Any]:
    # TODO: write function to retrieve album metadata from spotify
    pass


@celery_app.task(bind=True, ignore_result=False, serializer="json")
def fetch_album_playcount(self, album_id: str) -> Optional[Dict[str, Any]]:
    return spapi.album_playcount(album_id)


@celery_app.task(bind=True, task_time_limit=2, serializer="json")
def push_album(self, album: Dict[str, Any]) -> Dict[str, Any]:
    """
    Push album to db.
    """
    album_obj = parser.album.from_dict(obj_in=album)
    with session_scope() as db:
        db_album = crud.album.get(db, id=album_obj.id)
        if not db_album:
            # push album -> push album <> artists associations
            db_album = crud.album.create(db, obj_in=album_obj)
            association.push_album_x_artists(album=album, ignore_result=True)
        return jsonable_encoder(db_album)


@celery_app.task(bind=True, task_time_limit=2, serializer="json")
def update_album(self, album: Dict[str, Any]) -> Dict[str, Any]:
    album_obj = parser.album.from_album_playcount(obj_in=album)
    with session_scope() as db:
        db_album = crud.album.get(db, id=album_obj.id)
        db_album = crud.album.update(db, db_obj=db_album, obj_in=album_obj)
        return jsonable_encoder(db_album)


@celery_app.task(bind=True, ignore_result=True, serializer="json")
def flow_update_album(self, album_id: str) -> None:
    workflow = fetch_album_playcount.si(album_id=album_id) | update_album.s()
    workflow.apply_async()


@celery_app.task(bind=True, ignore_result=True, serializer="json")
def flow_album(
    self,
    album_id: str = None,
    album: Dict[str, Any] = None,
    check_db_first: Optional[bool] = False,
) -> None:
    """
    Workflow to push album metadata to db.
    """
    if check_db_first:
        with session_scope() as db:
            if album:
                album_obj = parser.album.from_dict(obj_in=album)
                db_album = crud.album.get(db, id=album_obj.id)
            else:
                db_album = crud.album.get(db, id=album_id)

            if db_album:
                # Album already in db
                return None

    if album_id and not album:
        album = spapi.album_playcount(album_id=album_id)

    artists = parser.artist.from_album(obj_in=album)
    if artists:
        artists_tasks = group(
            artist.flow_artist.si(
                artist_id=a.id, check_db_first=True, push_related_artists=True
            )
            for a in artists
        )
        workflow = artists_tasks | push_album.si(album=album)
    else:
        workflow = push_album.si(album=album)
    workflow.apply_async()

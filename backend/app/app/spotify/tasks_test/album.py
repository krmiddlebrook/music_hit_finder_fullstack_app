from typing import List, Optional, Dict, Any, Union

from celery import group, chord
from celery.utils.log import get_task_logger
from datetime import date, timedelta

from app.core.celery_app import celery_app
from app.db.session import session_scope

from app import crud, schemas
from app.spotify import parser
from ..spapi import spapi

from .track import push_tracks_playcounts

logger = get_task_logger(__name__)


@celery_app.task(bind=True)
def flow_scrape_album_playcounts(
    self,
    min_date: date = date.today() - timedelta(days=365),
    max_date: date = date.today(),
    skip: Optional[int] = 0,
    limit: Optional[int] = 50_000,
) -> None:
    """
    Collect album track playcounts.

    The flow performs the following steps:
        get album ids (only include albums by verified artists)
        for each album id:
            get tracks playcounts
        for each track:
            chain(
                push_track (if necessary),
                push_track_playcount
            )
                
    repeat: 2/week
    """
    with session_scope() as db:
        album_ids = [
            a.id
            for a in crud.album.get_albums_by_verified_artists(
                db, min_date=min_date, max_date=max_date, skip=skip, limit=limit
            )
        ]

    logger.info(f"Collecting album playcounts for {len(album_ids)} ")

    for album_id in album_ids:
        push_album_playcount.si(album_id).apply_async()

    logger.info(f"ALBUM PLAYCOUNTS TASKS called for ({len(album_ids)}) albums.")


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def read_album_playcount(self, album_id: str):
    playcounts = spapi.album_playcount(album_id)
    return playcounts


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_album_playcount(
    self, album_id: Optional[str] = None, album: Optional[schemas.Album] = None,
) -> None:
    if not album and not album_id:
        raise ValueError("Must pass value for one of either album_id or album.")
    elif album:
        album_id = album.id

    # TODO: add function to push/update album label and make it a group with
    # push_tracks_playcounts
    flow = read_album_playcount.si(album_id) | push_tracks_playcounts.s()
    flow.apply_async()


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_album_label(self, album_playcount: Dict[str, Any]):
    # TODO: need to figure out how to do this without slowing the playcounts down.
    raise NotImplementedError


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_album(
    self, album: Union[Dict[str, Any], schemas.Album]
) -> Optional[schemas.Album]:
    if isinstance(album, dict):
        album = parser.album.from_dict(obj_in=album)

    if not album:
        logger.warning("ALBUM is None!")
        return

    with session_scope() as db:
        db_obj = crud.album.get(db, id=album.id)

        if not db_obj:
            # Push the label if necessary
            if album.label:
                if crud.label.get_by_name(db, name=album.label):
                    crud.label.create(db, obj_in=schemas.LabelCreate(name=album.label))

            crud.album.create(db, obj_in=album)
            push_album_playcount.si(album.id).apply_async()
        elif album.label:
            if db_obj.label != album.label and album.label:
                if crud.label.get_by_name(db, name=album.label):
                    crud.label.create(db, obj_in=schemas.LabelCreate(name=album.label))

                db_obj.label = album.label
                db.commit()

    return album

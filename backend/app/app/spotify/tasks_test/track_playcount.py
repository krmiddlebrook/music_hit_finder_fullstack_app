from typing import List, Optional, Dict, Any, Union
from datetime import datetime


from celery import chord, group
from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.db.session import session_scope

from app import crud, schemas
from app.spotify import parser

# from app.spotify.track import push_track


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_tracks_playcounts(
    self, album: Dict[str, Any]
) -> Optional[schemas.TrackPlaycount]:
    tracks = parser.track.from_album_playcount(obj_in=album)
    tracks_plays = parser.track_playcount.from_album(obj_in=album)

    if not tracks_plays or not tracks or len(tracks_plays) != len(tracks):
        return

    # for t, tp in zip(tracks, tracks_plays):
    #     (push_track.si(t) | push_track_playcount.si(tp)).apply_async()

    return tracks_plays


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_track_playcount(
    self, track: schemas.TrackPlaycount
) -> Optional[schemas.TrackPlaycount]:
    with session_scope() as db:
        if not crud.track_playcount.get(db, id=track.id):
            crud.track_playcount.create(db, obj_in=track)

    return track

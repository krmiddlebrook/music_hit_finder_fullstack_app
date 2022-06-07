from typing import List, Optional, Dict, Any, Union

from celery import group
from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.db.session import session_scope

from app import crud, schemas, models, push
from app.spotify import parser
from app.spotify.spotify_mux import SpotifyMux

from app.spotify.association import push_artist_x_genres

logger = get_task_logger(__name__)


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_genres(self, genres: List[schemas.Genre]) -> List[models.Genre]:
    db_genres = []
    with session_scope() as db:
        for g in genres:
            db_genre = push.genre.push_genre(db, genre=g)
            db_genres.append(db_genre)

        return db_genres

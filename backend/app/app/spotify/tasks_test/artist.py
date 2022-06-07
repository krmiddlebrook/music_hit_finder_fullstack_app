from typing import List, Optional, Dict, Any

from celery import chord, group
from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.db.session import session_scope

from app import crud, schemas
from app.spotify import parser
from ..spapi import spapi
from .genre import push_genres_artist
import random

logger = get_task_logger(__name__)


# TODO: finish flow for scrapping artist (cities and links)
# @celery_app.task(bind=True)
# def flow_scrape_artists(self, playlist_track_limit: int = 500) -> None:
#     """
#     Collect tracks on playlists from Spotify.

#     Note: This task should be run after the playlists task.

#     The flow performs the following steps:
#         get playlist ids
#         for each playlist id:
#             get playlist tracks
#         for each track:
#             chain(
#                 push album artist(s) and track artist(s) to db
#                 push album to db
#                 push track to db
#                 group(
#                     push album <> artist(s) to db
#                     push track <> artist(s) to db
#                     push track <> playlist to db
#                 )
#             )

#     repeat: 1/week
#     """
#     with session_scope() as db:
#         playlists_ids = [p.id for p in crud.playlist.get_multi(db, skip=0, limit=10)]

#     logger.info(f"Collecting tracks for {len(playlists_ids)} playlist!")
#     for i, play_id in enumerate(playlists_ids):
#         (
#             read_playlist_tracks.s(play_id, i, playlist_track_limit)
#             | push_playlist_tracks.s(play_id)
#         ).apply_async()

#     logger.info("PLAYLIST TASKS called!")


# TODO: Make parser for artist stat, artist link, genre_artist, city,
# city_count, city_artist
@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def read_artist_info(self, artist_id: str) -> Optional[Dict[str, Any]]:
    return spapi.artist_info(artist_id)


# @celery_app.task(bind=True, task_time_limit=30, ignore_result=True)
# def read_artist_about(
#     self, artist_id: str, spm_iter: int = 0, limit: int = 500
# ) -> List[Dict[str, Any]]:

#     artists = spapi.artist_info(artist_id)


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_artists(self, artists: schemas.Artist) -> List[schemas.Artist]:
    for a in artists:
        push_artist.si(a).apply_async()

    return artists


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_artist(self, artist: schemas.Artist) -> Optional[schemas.Artist]:
    with session_scope() as db:
        db_obj = crud.artist.get(db, id=artist.id)
        if not db_obj:
            db_obj = crud.artist.create(db, obj_in=artist)
            # logger.info(f"Artist created {artist}!")

            push_genres_artist.si(artist.id, random.randint(0, 10)).apply_async()

        if (db_obj.verified is None and artist.verified) or (
            db_obj.active is None and artist.active
        ):
            db_obj = crud.artist.update_status(
                db, db_obj=db_obj, new_info=artist.dict()
            )
            # logger.info(
            #     f"Updated artist info: ({db_obj.id}, {db_obj.verified}, {db_obj.active})"
            # )
    return artist

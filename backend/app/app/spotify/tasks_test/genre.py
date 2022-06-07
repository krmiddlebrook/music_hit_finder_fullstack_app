from typing import List, Optional, Dict, Any, Union

from celery import group
from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.db.session import session_scope

from app import crud, schemas
from app.spotify import parser
from ..spotify_mux import SpotifyMux

from .association import push_artist_x_genres

logger = get_task_logger(__name__)


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
def push_genres_artist(self, artist_id: str, spm_iter: int = 0) -> List[schemas.Genre]:
    artist = SpotifyMux(spm_iter).artist_about(artist_id)
    if not artist:
        return []

    genres = parser.genre.from_artist_about(obj_in=artist)
    (push_genres.si(genres) | push_artist_x_genres.si(genres, artist_id)).apply_async()
    return genres


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_genres(
    self, genres: Union[List[Dict[str, Any]], List[schemas.Genre]]
) -> List[schemas.Genre]:
    if genres:
        if isinstance(genres[0], dict):
            genres = parser.genre.from_genre_list(obj_in=genres)

    group(push_genre.si(g) for g in genres).apply_async(serializer="pickle")
    return genres


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_genre(
    self, genre: Union[Dict[str, Any], schemas.Genre]
) -> Optional[schemas.Genre]:
    # logger.info(f"GENRE: {genre}")
    if isinstance(genre, dict):
        genre = parser.genre.from_dict(obj_in=genre)

    if not genre:
        logger.warning("GENRE is None!")
        return

    with session_scope() as db:
        if not crud.genre.get(db, id=genre.id):
            crud.genre.create(db, obj_in=genre)
            # logger.info(f"Genre created {genre}!")
    return genre

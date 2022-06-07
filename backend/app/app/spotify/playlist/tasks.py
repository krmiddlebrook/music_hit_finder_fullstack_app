from datetime import datetime
from typing import List, Optional, Dict, Any
from psycopg2.errors import UniqueViolation

from celery import chord, group
from celery.utils.log import get_task_logger

from app.spotify.spotify_mux import spotify_mux
from app.spotify.utils import chunkify, flow_complete

from app.core.celery_app import celery_app
from app.db.session import session_scope

# from sqlalchemy.orm import Session

from app import crud, schemas, models
from app.spotify import parser
from app.spotify.association import push_term_x_playlist


logger = get_task_logger(__name__)


@celery_app.task(bind=True, ignore_result=True)
def flow_scrape_playlists(self, term_playlist_limit: int = 1_000):
    """ 
    A flow to collect Spotify playlists using a set of search terms.

    Ingest search terms -> get search term playlists ->
    parse playlists data -> push results to db
    
    repeat: 1/week
    """
    logger.info(f"Chunking search terms from db: {models.Search_Term.__tablename__}")

    with session_scope() as db:
        search_terms = [
            term.id for term in crud.search_term.get_multi(db, skip=0, limit=None)
        ]

    for i, term in enumerate(search_terms):
        # get search_term playlist ->
        # push playlist owner to db ->
        # push playlist to db -> group(
        #   push playlist follower count to db,
        #   push search_term <> playlist to db
        # )
        (
            read_search_term_playlists.s(term, i, term_playlist_limit)
            | push_search_term_playlists.s(term)
        ).apply_async()


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def read_search_term_playlists(
    self, search_term: str, spm_iter: int = 0, limit: int = 500
) -> List[Dict[str, Any]]:
    return spotify_mux.search_term_playlists(search_term, limit)


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_search_term_playlists(
    self, playlists: List[Dict[str, Any]], search_term: str
) -> List[Dict[str, Any]]:
    for p in playlists:
        push_search_term_playlist.si(p, search_term).apply_async()

    return playlists


# TODO: Make this a celery task
@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_search_term_playlist(
    self, playlist: Dict[str, Any], search_term: str
) -> Dict[str, Any]:
    workflow = (
        push_playlist_owner.si(playlist)
        | push_playlist.si(playlist)
        | group(
            push_playlist_followers_count.si(playlist),
            push_term_x_playlist.si(playlist, search_term),
        )
    )
    workflow.apply_async()

    return playlist


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True)
def push_playlist_owner(
    self, playlist: Dict[str, Any]
) -> Optional[schemas.SpotifyUser]:
    spot_user = parser.spotify_user.from_search_term_playlist(obj_in=playlist)
    if not spot_user:
        return

    # Check if user exists in the spotify users table.
    with session_scope() as db:
        if not crud.spotify_user.get(db, id=spot_user.id):
            crud.spotify_user.create(db, obj_in=spot_user)

    return spot_user


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_playlist(self, playlist: Dict[str, Any]) -> Optional[schemas.Playlist]:
    play_obj = parser.playlist.from_playlist(obj_in=playlist)
    if not play_obj:
        logger.warning(f"Playlist is None! {playlist}")
        return

    # Check if user exists in the spotify users table.
    with session_scope() as db:
        # Add playlist to the playlists table.
        if not crud.playlist.get(db, id=play_obj.id):
            # Add playlist to the playlists list.
            crud.playlist.create(db, obj_in=play_obj)

    return play_obj


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_playlist_followers_count(
    self, playlist: Dict[str, Any]
) -> Optional[schemas.PlaylistFollowersCount]:
    p_fcnt = parser.playlist_followers_count.from_playlist(obj_in=playlist)
    if not p_fcnt:
        return

    # Check if user exists in the spotify users table.
    with session_scope() as db:
        # Add playlist to the playlists table.
        if not crud.playlist_followers_count.get(db, id=p_fcnt.id):
            # Add playlist to the playlists list.
            crud.playlist_followers_count.create(db, obj_in=p_fcnt)

    return p_fcnt

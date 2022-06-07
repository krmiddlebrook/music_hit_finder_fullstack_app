from typing import List, Dict, Any, Optional
import time

from celery.utils.log import get_task_logger
from celery import group
from celery.result import AsyncResult
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.core.celery_app import celery_app
from app.db.session import session_scope

from app import schemas, models, crud
from app.spotify.spotify_mux import spotify_mux
from app.spotify import parser
from app import spotify

# from app.spotify import artist

logger = get_task_logger(__name__)


@celery_app.task(bind=True, ignore_result=False, serializer="json")
def fetch_tracks_data(self, track_ids: List[str]) -> List[Dict[str, Any]]:
    return spotify_mux.tracks(track_ids)


@celery_app.task(bind=True, ignore_result=False, serializer="json")
def fetch_track_data(self, track_id: str) -> Dict[str, Any]:
    return spotify_mux.track(track_id)


@celery_app.task(
    bind=True, task_time_limit=3, serializer="json", queue="short-queue",
)
def push_track(self, track: Dict[str, Any],) -> Dict[str, Any]:
    """
    Push track to db.
    """
    t_obj = parser.track.from_dict(obj_in=track)
    with session_scope() as db:
        db_track = crud.track.get(db, id=t_obj.id)
        if not db_track:
            crud.track.create(db, obj_in=t_obj)
            # association.push_track_x_artists(track=track)
        else:
            db_track = crud.track.update(db, db_obj=db_track, obj_in=t_obj)
        spotify.association.push_track_x_artists(track=track)
        return jsonable_encoder(db_track)


@celery_app.task(bind=True, task_time_limit=3, serializer="json")
def flow_track(
    self,
    track: Dict[str, Any],
    artist_check_db_first: bool = True,
    push_related_artists: bool = True,
    push_discography: bool = True,
    album_check_db_first: bool = True,
) -> None:
    """
    Workflow to push track metadata to the db.
    """
    # artists -> album -> track -> track associations
    artists = parser.artist.from_track(obj_in=track)
    if artists:
        artists_tasks = group(
            spotify.artist.flow_artist.si(
                artist_id=a.id,
                check_db_first=artist_check_db_first,
                push_related_artists=push_related_artists,
                push_discography=push_discography,
            )
            for a in artists
        )
        workflow = artists_tasks | spotify.album.flow_album.si(
            album=track, check_db_first=album_check_db_first
        )
    else:
        workflow = spotify.album.flow_album.si(
            album=track, check_db_first=album_check_db_first
        )

    workflow = workflow | push_track.si(track=track)
    workflow.apply_async()
    # return workflow()


@celery_app.task(bind=True, ignore_result=True, serializer="json")
def flow_track_playlist(self, track: Dict[str, Any], playlist_id: str) -> None:
    """
    Workflow to push track metadata with playlist association to the db.
    """
    t_obj = parser.track.from_dict(obj_in=track)

    artists = parser.artist.from_track(obj_in=track)
    # artists -> album -> track -> track associations
    if artists:
        # TODO; switch check_db_first to true after running this a few times
        # to populate the db
        artists_tasks = group(
            spotify.artist.flow_artist.si(
                artist_id=a.id,
                check_db_first=True,
                push_related_artists=True,
                push_discography=True,
            )
            for a in artists
        )
        workflow = artists_tasks | spotify.album.flow_album.si(
            album=track, check_db_first=True
        )
    else:
        workflow = spotify.album.flow_album.si(album=track, check_db_first=False)

    workflow = (
        workflow
        | push_track.si(track=track)
        | spotify.association.push_track_x_playlist.si(
            track_id=t_obj.id, playlist_id=playlist_id
        )
    )
    workflow.apply_async()
    # return workflow()


@celery_app.task(bind=True, task_time_limit=1, serializer="json", queue="short-queue")
def update_track(self, track: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    track = parser.track.from_dict(obj_in=track)
    with session_scope() as db:
        db_track = crud.track.get(db, track.id)
        if not db_track:
            logger.warning(f"Track not found in DB! ({track.id})")
            return {"track_id": db_track.id, "success": False}
        db_track = crud.track.update(db, db_obj=db_track, obj_in=track)
        return {"track_id": db_track.id, "success": True}


@celery_app.task(bind=True, task_time_limit=10, serializer="json")
def update_tracks(self, tracks_data: List[Dict[str, Any]]) -> Dict[str, bool]:
    """
    Send request to Spotify API for tracks metadata. Process metadata and push (in bulk)
    results to db.
    """
    tracks = []
    albums = {}
    artists = {}
    for t in tracks_data:
        if isinstance(t, dict):
            t_obj = parser.track.from_dict(obj_in=t)
            if t_obj:
                tracks.append(jsonable_encoder(t_obj))
            al_obj = parser.album.from_dict(obj_in=t)
            if al_obj:
                albums[al_obj.id] = jsonable_encoder(al_obj)
            a_objs = parser.artist.from_track(obj_in=t)
            if a_objs:
                for a_obj in a_objs:
                    artists[a_obj.id] = jsonable_encoder(a_obj)
                print("~" * 100)
                print(a_objs)
                print("~" * 100)

    result = {}
    with session_scope() as db:
        art_missing_ids = set(
            crud.artist.get_missing_ids_by_ids(db, ids=list(artists.keys()))
        )
        missing_artists = [a for aid, a in artists.items() if aid in art_missing_ids]
        artists_success = crud.artist.create_multi(db, objs_in=missing_artists)
        result["artists_success"] = artists_success
        al_missing_ids = set(
            crud.album.get_missing_ids_by_ids(db, ids=list(albums.keys()))
        )
        missing_albums = [al for alid, al in albums.items() if alid in al_missing_ids]
        albums_success = crud.album.create_multi(db, objs_in=missing_albums)
        result["albums_success"] = albums_success

        update_succeeded = crud.track.update_multi(db, objs_in=tracks)
        result["track_success"] = update_succeeded
        return result


# @celery_app.task(bind=True, serializer="json")
def flow_tracks(track_ids: List[str]) -> None:
    """
    Workflow to fetch track data and push it to the db.

    Parameters:
        `track_ids`: A list of spotify track ids (max 50 track ids).
    """
    # (max 50 tracks per request).
    workflow = fetch_tracks_data.si(track_ids=track_ids) | update_tracks.s()
    workflow.apply_async(ignore_result=True)
    # return workflow.apply_async()

from typing import List, Dict, Any, Optional, Union
import time

from celery.utils.log import get_task_logger
from celery import group
from celery.result import AsyncResult
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import session_scope

from app import schemas, models, crud
from app.spotify.spotify_mux import spotify_mux
from app.spotify import parser
from app.spotify import association
from app import spotify


logger = get_task_logger(__name__)


@celery_app.task(bind=True, ignore_result=False, serializer="json")
def fetch_user_playlists(self, track_ids: List[str]) -> List[Dict[str, Any]]:
    # TODO: change this spotify_mux request
    return spotify_mux.tracks(track_ids)


@celery_app.task(bind=True, ignore_result=False, serializer="json")
def fetch_playlist_tracks(self, playlist_id: str) -> Dict[str, Any]:
    # TODO: change this spotify_mux request
    return spotify_mux.track(playlist_id)


# @celery_app.task(
#     bind=True, task_time_limit=3, serializer="json", queue="short-queue",
# )
def push_user_tracks(
    spotify_id: str,
    tracks: List[Dict[str, Any]],
    top_track: Optional[bool] = False,
    source: Optional[str] = None,
) -> Any:
    """
    Push spotify_user <> track associations to db.
    """
    tasks = []
    for track in tracks:
        # push track
        track_obj = parser.track.from_dict(obj_in=track)
        artists_objs = parser.artist.from_track(obj_in=track)
        album_obj = parser.album.from_dict(obj_in=track)
        # Push artists -> album -> track -> spectrogram flow -> push user <> track to db
        for a in artists_objs:
            spotify.artist.push_artist.si(
                artist=jsonable_encoder(a),
                push_related_artists=False,
                push_discography=False,
            ).apply_async(ignore_result=True)
        spotify.album.push_album.si(album=jsonable_encoder(album_obj)).apply_async(
            ignore_result=True
        )
        # workflow = (
        #     artists_flow
        #     | spotify.album.push_album.si(album=jsonable_encoder(album_obj))
        #     | spotify.track.push_track.si(track=jsonable_encoder(track_obj))
        # )
        workflow = spotify.track.push_track.si(
            track=jsonable_encoder(track_obj)
        ) | spotify.association.push_track_x_user.si(
            track_id=track_obj.id,
            user_id=spotify_id,
            top_track=top_track,
            source=source,
        )
        # Push spectrograms (download wav -> create spec -> push to db)
        if track_obj.preview_url is not None:
            workflow = workflow | spotify.spectrogram.flow_spectrogram.si(
                track_id=track_obj.id,
                preview_url=track_obj.preview_url,
                check_db_first=True,
            )
        tasks.append(workflow)
    tasks = group(tasks).apply_async()
    # TODO: may want to remove this get and instead wait until ready
    results = tasks.get()
    logger.info("PUSH USER TRACKS COMPLETE!")
    return results


@celery_app.task(bind=True, ignore_result=False, serializer="json")
def fetch_canidate_track_pairs_by_users(
    self,
    spotify_ids: Union[List[str], str],
    lag_period: int = 30,
    days_since_release: int = 180,
    canidate_hit_limit: int = 10_000,
    skip: int = 0,
) -> List[Dict[str, Any]]:
    with session_scope() as db:
        # Get canidate hit <> user track distance pairs.
        td_canidate_pairs = crud.user.get_canidate_track_pairs_by_users(
            db,
            spotify_ids=spotify_ids,
            lag_period=lag_period,
            days_since_release=days_since_release,
            canidate_hit_limit=canidate_hit_limit,
            limit=int(canidate_hit_limit * 3),
            skip=0,
        )
        return td_canidate_pairs


@celery_app.task(bind=True, ignore_result=False, serializer="json")
def push_canidate_track_pairs(self, canidates: List[Dict[str, Any]]) -> Any:
    """
    Compute canidate hit <> user track distances and push to db.
    """
    chunked_pairs = spotify.utils.chunkify(
        canidates, chunk_size=settings.MAX_BATCH_SIZE
    )
    # TODO: optional to wait until this task completes
    dist_tasks = group(
        spotify.track_distance.flow_tracks_distances.si(track_ids=pairs)
        for pairs in chunked_pairs
    ).apply_async()
    return dist_tasks


def build_push_user_tracks_tasks(
    spotify_id: str,
    tracks: List[Dict[str, Any]],
    top_track: Optional[bool] = False,
    source: Optional[str] = None,
) -> List[Any]:
    with session_scope() as db:
        db_track_users = crud.track_user.get_multi_by_user(
            db, user_spotify_id=spotify_id
        )
        db_tu_track_ids = set([tu.track_id for tu in db_track_users])

    push_tracks_tasks = []
    tracks_dict = {}
    artists_dict = {}
    albums_dict = {}
    for track in tracks:
        track_obj = parser.track.from_dict(obj_in=track)
        if track_obj.id not in db_tu_track_ids:
            if track_obj:
                tracks_dict[track_obj.id] = track_obj
            artists_objs = parser.artist.from_track(obj_in=track)
            for a in artists_objs:
                artists_dict[a.id] = a
            album_obj = parser.album.from_dict(obj_in=track)
            if album_obj:
                albums_dict[album_obj.id] = album_obj

    with session_scope() as db:
        db_missing_artist_ids = set(
            crud.artist.get_missing_ids_by_ids(db, ids=list(artists_dict.keys()))
        )
        db_missing_album_ids = set(
            crud.album.get_missing_ids_by_ids(db, ids=list(albums_dict.keys()))
        )
        db_tracks = crud.track.get_multi_by_ids(db, ids=list(tracks_dict.keys()))
        db_tracks_dict = {db_t.id: db_t for db_t in db_tracks}
        db_track_ids = set([t.id for t in db_tracks])
        db_tracks_specs = crud.spectrogram.get_by_track_ids_simplified(
            db, track_ids=list(tracks_dict.keys())
        )
        db_track_ids_specs = set([t.id for t in db_tracks_specs])

        filtered_artists = [
            jsonable_encoder(a_obj)
            for aid, a_obj in artists_dict.items()
            if aid in db_missing_artist_ids
        ]
        db_artists_succeeded = crud.artist.create_multi(db, objs_in=filtered_artists)
        filtered_albums = [
            jsonable_encoder(al_obj)
            for alid, al_obj in albums_dict.items()
            if alid in db_missing_album_ids
        ]
        db_albums_succeeded = crud.album.create_multi(db, objs_in=filtered_albums)
        print("~" * 100)
        print(
            f"BULK DB Artist Insert Succeeded: ({db_artists_succeeded}, {len(filtered_artists)})"
        )
        print(
            f"BULK DB Album Insert Succeeded: ({db_albums_succeeded}, {len(filtered_albums)})"
        )
        print("~" * 100)
        print("\n")
        # Determine the workflow for each track
        for tid, t_obj in tracks_dict.items():
            # Push spectrograms (download wav -> create spec -> push to db)
            workflow = None
            if tid not in db_track_ids:
                # Push track to the db if it doesn't exist
                workflow = spotify.track.push_track.si(track=jsonable_encoder(t_obj))
            elif not db_tracks_dict[tid].preview_url and t_obj.preview_url:
                # Update the track with the new data
                workflow = spotify.track.push_track.si(track=jsonable_encoder(t_obj))

            if tid not in db_track_ids_specs and t_obj.preview_url:
                if workflow:
                    # Append spec flow to the task flow
                    workflow = workflow | spotify.spectrogram.flow_spectrogram.si(
                        track_id=t_obj.id,
                        preview_url=t_obj.preview_url,
                        check_db_first=True,
                    )
                else:
                    # Run spec flow
                    workflow = spotify.spectrogram.flow_spectrogram.si(
                        track_id=t_obj.id,
                        preview_url=t_obj.preview_url,
                        check_db_first=True,
                    )

            if workflow:
                # Append the push_track_user task
                workflow = workflow | spotify.association.push_track_x_user.si(
                    track_id=t_obj.id,
                    user_id=spotify_id,
                    top_track=top_track,
                    source=source,
                )
            else:
                # Set flow to run push_track_user task
                workflow = spotify.association.push_track_x_user.si(
                    track_id=t_obj.id,
                    user_id=spotify_id,
                    top_track=top_track,
                    source=source,
                )
            push_tracks_tasks.append(workflow)
    return push_tracks_tasks


def update_user_canidate_tracks(
    spotify_id: str,
    tracks: List[Dict[str, Any]],
    top_track: Optional[bool] = False,
    source: Optional[str] = None,
    lag_period: int = 30,
    days_since_release: int = 180,
    canidate_hit_limit: int = 5_000,
    skip: int = 0,
    wait_until_complete: bool = False,
) -> Any:
    """
    Update a spotify user's potential hit recommendations by pushing their tracks,
    creating spectrograms, computing missing track distance pairs, and pushing
    results to the db.
    """
    # Push user tracks to track_user table
    # Get missing canidate hit <> user track distance pairs.
    # Compute canidate hit <> user track distances and push them to the db
    workflow = (
        group(
            build_push_user_tracks_tasks(
                spotify_id=spotify_id, tracks=tracks, top_track=top_track, source=source
            )
        )
        | fetch_canidate_track_pairs_by_users.si(
            spotify_ids=[spotify_id],
            lag_period=lag_period,
            days_since_release=days_since_release,
            canidate_hit_limit=canidate_hit_limit,
            skip=skip,
        )
        | push_canidate_track_pairs.s()
    )

    if not wait_until_complete:
        workflow.apply_async(ignore_result=True)
        return

    # WARNING: waiting until this long task completes could block other tasks from
    # running proceed with caution!
    logger.warning(
        "You are waiting until all subtasks in this task complete. This is not ",
        "recommended, as it may block other tasks from running.",
    )
    workflow = workflow.apply_async()
    results = workflow.get()
    return results

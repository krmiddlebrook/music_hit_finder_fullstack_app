from typing import List, Optional, Dict, Any

from celery import chord, group, chain
from celery.utils.log import get_task_logger
from celery.result import AsyncResult
from fastapi.encoders import jsonable_encoder

from app.spotify.spotify_mux import SpotifyMux

from app.core.celery_app import celery_app
from app.db.session import session_scope

from app import crud
from app.spotify import parser
from app.spotify.spotify_mux import spotify_mux
from app.spotify import track, association

logger = get_task_logger(__name__)


@celery_app.task(bind=True, task_time_limit=10, ignore_result=False, serializer="json")
def fetch_playlist_tracks(
    self, playlist_id: str, limit: int = 300
) -> List[Dict[str, Any]]:
    return spotify_mux.playlist_tracks(playlist_id=playlist_id, limit=limit)


@celery_app.task(
    bind=True, task_time_limit=int(60 * 2.5), ignore_result=False, serializer="json"
)
def push_playlist_tracks(self, tracks: List[Dict[str, Any]], playlist_id: str) -> int:
    new_tracks = 0
    valid_tracks = {}
    artists = {}
    albums = {}
    for t in tracks:
        t_obj = parser.track.from_dict(obj_in=t)
        if t_obj:
            valid_tracks[t_obj.id] = t_obj
            t_artists = parser.artist.from_track(obj_in=t, include_album_artists=True)
            for t_art in t_artists:
                artists[t_art.id] = jsonable_encoder(t_art)
            album = parser.album.from_track(obj_in=t)
            if album:
                albums[album.id] = jsonable_encoder(album)

    with session_scope() as db:
        missing_artist_ids = set(
            crud.artist.get_missing_ids_by_ids(db, ids=list(artists.keys()))
        )
        missing_artists = [a for aid, a in artists.items() if aid in missing_artist_ids]
        _ = crud.artist.create_multi(db, objs_in=missing_artists)
        missing_album_ids = set(
            crud.album.get_missing_ids_by_ids(db, ids=list(albums.keys()))
        )
        missing_albums = [
            al for alid, al in albums.items() if alid in missing_album_ids
        ]
        # TODO: add artist ids to albums
        _ = crud.album.create_multi(db, objs_in=missing_albums)

        # TODO: add artist ids to tracks
        missing_track_ids = set(
            crud.track.get_missing_ids_by_ids(db, ids=list(valid_tracks.keys()))
        )
        missing_tracks = [
            t for tid, t in valid_tracks.items() if tid in missing_track_ids
        ]
        new_tracks = len(missing_tracks)
        _ = crud.track.create_multi(db, objs_in=missing_tracks)
        _ = crud.track_playlist.create_multi_from_playlist_ids(
            db, playlist_ids_track_ids={playlist_id: set(valid_tracks.keys())}
        )
        return new_tracks


# @celery_app.task(bind=True, task_time_limit=6, ignore_result=True, serializer="json")
def flow_playlist_tracks(playlist_id: str, track_limit: int = 300) -> None:
    workflow = fetch_playlist_tracks.si(
        playlist_id=playlist_id, limit=track_limit
    ) | push_playlist_tracks.s(playlist_id=playlist_id)
    workflow.apply_async(ignore_result=True)
    # return workflow()

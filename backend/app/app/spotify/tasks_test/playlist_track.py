from typing import List, Optional, Dict, Any

from celery import chord, group, chain
from celery.utils.log import get_task_logger

from ..spotify_mux import SpotifyMux
from .association import (
    push_album_x_artists,
    push_track_x_artists,
    push_track_x_playlist,
)

# from app.spotify.artist import push_artists
# from app.spotify.album import push_album
from .track import push_track

# from .utils import chunkify, flow_complete

from app.core.celery_app import celery_app
from app.db.session import session_scope

# from sqlalchemy.orm import Session

from app import crud
from app.spotify import parser

logger = get_task_logger(__name__)


@celery_app.task(bind=True)
def flow_scrape_playlists_tracks(self, playlist_track_limit: int = 300) -> None:
    """
    Collect tracks on playlists from Spotify.

    Note: This task should be run after the playlists task.

    The flow performs the following steps:
        get playlist ids
        for each playlist id:
            get playlist tracks
        for each track:
            chain(
                push album artist(s) and track artist(s) to db
                push album to db
                push track to db
                group(
                    push album <> artist(s) to db
                    push track <> artist(s) to db
                    push track <> playlist to db
                )
            )

    repeat: 1/week
    """
    with session_scope() as db:
        playlists_ids = [
            p.id for p in crud.playlist.get_popular_playlists(db, skip=0, limit=1)
        ]

    logger.info(f"Collecting tracks for {len(playlists_ids)} playlist!")
    for i, play_id in enumerate(playlists_ids):
        (
            read_playlist_tracks.s(play_id, i, playlist_track_limit)
            | push_playlist_tracks.s(play_id)
        ).apply_async()

    logger.info("PLAYLIST TASKS called!")


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def read_playlist_tracks(
    self, playlist_id: str, spm_iter: int = 0, limit: int = 500
) -> List[Dict[str, Any]]:
    return SpotifyMux(spm_iter).playlist_tracks(playlist_id=playlist_id, limit=limit)


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_playlist_tracks(self, tracks: List[Dict[str, Any]], playlist_id: str) -> None:
    for t in tracks:
        push_playlist_track.si(t, playlist_id).apply_async()


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_playlist_track(
    self, track: Dict[str, Any], playlist_id: str
) -> Optional[Dict[str, Any]]:
    # artists = parser.artist.from_track(obj_in=track, include_album_artists=True)
    track = parser.track.from_dict(obj_in=track)
    if not track:
        logger.warning("Playlist Track is None!")
        return
    elif not track.album_id:
        logger.warning("Playlist Track album_id is None!")
        return
    elif not track.artists:
        logger.warning("Playlist Track artists is None!")
        return

    # workflow = (
    #     push_artists.si(artists)
    #     | push_album.si(track.get("album", {}))
    #     | push_track.si(track, artist_ids)
    #     | group(
    #         push_album_x_artists.si(
    #             track.get("album", {}).get("artists", []), album_id
    #         ),
    #         push_track_x_artists.si(track.get("artists", []), track["id"]),
    #         push_track_x_playlist.si(track["id"], playlist_id),
    #     )
    # )
    # workflow.apply_async()
    return track

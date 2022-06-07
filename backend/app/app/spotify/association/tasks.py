from typing import List, Optional, Dict, Any, Union

from fastapi.encoders import jsonable_encoder
from celery import chord, group
from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.db.session import session_scope
from sqlalchemy.orm import Session

from app import crud, schemas
from app.spotify import parser

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True, task_time_limit=2, serializer="json", queue="short-queue",
)
def push_term_x_playlist(self, playlist: Dict[str, Any], search_term: str) -> None:
    play_obj = parser.playlist.from_playlist(obj_in=playlist)

    if not play_obj:
        logger.warning("Playlist is None!")
        return

    # Add term <> playlist to the db.
    with session_scope() as db:
        if not crud.term_playlist.get(db, term_id=search_term, playlist_id=play_obj.id):
            term_play = schemas.TermPlaylist(
                term_id=search_term, playlist_id=play_obj.id
            )
            crud.term_playlist.create(db, obj_in=term_play)


def push_album_x_artists(
    album: Dict[str, Any], ignore_result: Optional[bool] = True
) -> None:
    album_obj = parser.album.from_dict(obj_in=album)
    artists = parser.artist.from_album(obj_in=album)

    for art in artists:
        push_album_x_artist.si(album_id=album_obj.id, artist_id=art.id).apply_async(
            ignore_result=ignore_result
        )


@celery_app.task(
    bind=True, task_time_limit=1, serializer="json", queue="short-queue",
)
def push_album_x_artist(self, album_id: str, artist_id: str) -> None:
    with session_scope() as db:
        if not crud.album_artist.get(db, album_id=album_id, artist_id=artist_id):
            crud.album_artist.create(db, album_id=album_id, artist_id=artist_id)


# @celery_app.task(bind=True, task_time_limit=5, ignore_result=False, serializer="json")
def push_track_x_artists(
    track: Dict[str, Any], ignore_result: Optional[bool] = True
) -> None:
    t = parser.track.from_dict(obj_in=track)
    artists = parser.artist.from_track(obj_in=track)
    for a in artists:
        push_track_x_artist.si(track_id=t.id, artist_id=a.id).apply_async(
            ignore_result=ignore_result
        )


@celery_app.task(
    bind=True, task_time_limit=1, serializer="json", queue="short-queue",
)
def push_track_x_user(
    self,
    track_id: str,
    user_id: str,
    top_track: Optional[bool] = False,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    with session_scope() as db:
        db_obj = crud.track_user.get(db, track_id=track_id, user_id=user_id)
        if not crud.track_user.get(db, track_id=track_id, user_id=user_id):
            db_obj = crud.track_user.create(
                db,
                track_id=track_id,
                user_id=user_id,
                top_track=top_track,
                source=source,
            )
        return jsonable_encoder(db_obj)


@celery_app.task(
    bind=True, task_time_limit=1, serializer="json", queue="short-queue",
)
def push_track_x_artist(self, track_id: str, artist_id: str) -> None:
    with session_scope() as db:
        if not crud.track_artist.get(db, track_id=track_id, artist_id=artist_id):
            t_art = schemas.TrackArtist(track_id=track_id, artist_id=artist_id)
            crud.track_artist.create(db, obj_in=t_art)


@celery_app.task(
    bind=True, task_time_limit=1, serializer="json", queue="short-queue",
)
def push_track_x_playlist(self, track_id: str, playlist_id: str) -> None:
    with session_scope() as db:
        if not crud.track_playlist.get(db, track_id=track_id, playlist_id=playlist_id):
            track_play = schemas.TrackPlaylist(
                track_id=track_id, playlist_id=playlist_id
            )
            crud.track_playlist.create(
                db, obj_in=track_play,
            )


def push_artist_x_genres(
    artist: Dict[str, Any], ignore_result: Optional[bool] = True
) -> None:
    artist = parser.artist.from_dict(obj_in=artist)

    for g in artist.genres:
        push_artist_x_genre.si(
            artist_id=artist.id, genre=jsonable_encoder(g)
        ).apply_async(ignore_result=ignore_result)

    # with session_scope() as db:
    #     for g in artist.genres:
    #         # Ensure the genre exists in db
    #         if not crud.genre.get(db, id=g.id):
    #             crud.genre.create(db, obj_in=g)

    #         if not crud.genre_artist.get(db, genre_id=g.id, artist_id=artist.id):
    #             crud.genre_artist.create(
    #                 db, genre_id=g.id, artist_id=artist.id,
    #             )
    # logger.info(f"Genre<>Artist pushed ({g.id}, {artist.id})!")


@celery_app.task(
    bind=True, task_time_limit=2, serializer="json", queue="short-queue",
)
def push_artist_x_genre(self, artist_id: str, genre: Dict[str, Any]) -> None:
    # On a large instance this task should be a normal celery task
    # but, on small instances, to avoid overwhelming the redis message broker
    # this task may need to be a normal python function instead. Since the
    # instance will have good internet connection it shouldn't effect task times
    # by more than a few milliseconds.

    with session_scope() as db:
        g = schemas.Genre(**genre)
        if not crud.genre.get(db, id=g.id):
            crud.genre.create(db, obj_in=g)

        if not crud.genre_artist.get(db, genre_id=g.id, artist_id=artist_id):
            crud.genre_artist.create(
                db, genre_id=g.id, artist_id=artist_id,
            )


# @celery_app.task(bind=True, task_time_limit=5,serializer="json")
def push_artist_x_links(
    artist: Union[Dict[str, Any], schemas.ArtistCreate],
    ignore_result: Optional[bool] = True,
) -> None:
    if isinstance(artist, dict):
        artist = parser.artist.from_dict(obj_in=artist)

    if artist.links:
        for link in artist.links:
            push_artist_x_link.si(link=jsonable_encoder(link)).apply_async(
                ignore_result=ignore_result
            )
            # crud.artist_link.create(db, obj_in=link)


@celery_app.task(
    bind=True, task_time_limit=1, serializer="json", queue="short-queue",
)
def push_artist_x_link(self, link: Dict[str, Any]) -> None:
    # On a large instance this task should be a normal celery task
    # but, on small instances, to avoid overwhelming the redis message broker
    # this task may need to be a normal python function instead. Since the
    # instance will have good internet connection it shouldn't effect task times
    # by more than a few milliseconds.
    with session_scope() as db:
        link = schemas.ArtistLink(**link)
        crud.artist_link.create(db, obj_in=link)


@celery_app.task(
    bind=True, task_time_limit=4, serializer="json", queue="short-queue",
)
def simple_push_album(
    self, album: Dict[str, Any], artist_ids: Optional[List[str]] = None
) -> None:
    album = schemas.Album(**album)
    with session_scope() as db:
        if not crud.album.get(db, id=album.id):
            crud.album.create(db, obj_in=album)
            if artist_ids:
                for aid in artist_ids:
                    push_album_x_artist.si(
                        album_id=album.id, artist_id=aid
                    ).apply_async(ignore_result=True)


@celery_app.task(
    bind=True, task_time_limit=4, serializer="json", queue="short-queue",
)
def simple_push_track(
    self, track: Dict[str, Any], artist_ids: Optional[List[str]] = None
) -> None:
    track = schemas.Track(**track)
    with session_scope() as db:
        if not crud.track.get(db, id=track.id):
            crud.track.create(db, obj_in=track)
            if artist_ids:
                for aid in artist_ids:
                    push_track_x_artist.si(
                        track_id=track.id, artist_id=aid
                    ).apply_async(ignore_result=True)

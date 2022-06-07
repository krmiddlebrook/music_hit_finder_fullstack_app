from typing import List, Optional, Dict, Any, Union

from celery import chord, group
from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.db.session import session_scope

from app import crud, schemas
from app.spotify import parser

logger = get_task_logger(__name__)


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_term_x_playlist(
    self, playlist: Union[Dict[str, Any], schemas.Playlist], search_term: str
) -> Optional[schemas.TermPlaylist]:
    if isinstance(playlist, dict):
        play_obj = parser.playlist.from_playlist(obj_in=playlist)

    if not play_obj:
        logger.warning("Playlist is None!")
        return

    # Add term <> playlist to the db.
    term_play = schemas.TermPlaylist(term_id=search_term, playlist_id=play_obj.id)
    with session_scope() as db:
        if not crud.term_playlist.get(
            db, term_id=term_play.term_id, playlist_id=term_play.playlist_id
        ):
            crud.term_playlist.create(db, obj_in=term_play)

    return term_play


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_album_x_artists(
    self, artists: Union[List[Dict[str, Any]], List[schemas.Artist]], album_id: str
) -> List[schemas.AlbumArtist]:
    album_artists = []

    if artists:
        if isinstance(artists[0], dict):
            artists = parser.artist.from_artist_list(obj_in=artists)
    else:
        return album_artists

    with session_scope() as db:
        for art in artists:
            al_art_obj = schemas.AlbumArtist(album_id=album_id, artist_id=art.id)
            album_artists.append(al_art_obj)

            if crud.album_artist.get(db, album_id=album_id, artist_id=art.id):
                continue

            crud.album_artist.create(db, obj_in=al_art_obj)
            # logger.info(f"Album<>Artist pushed ({album_id}, {art.id})!")

    return album_artists


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_track_x_artists(
    self, artists: Union[List[Dict[str, Any]], List[schemas.Artist]], track_id: str
) -> List[schemas.TrackArtist]:
    track_artists = []

    if artists:
        if isinstance(artists[0], dict):
            artists = parser.artist.from_artist_list(obj_in=artists)
    else:
        return track_artists

    with session_scope() as db:
        for art in artists:
            t_art_obj = schemas.TrackArtist(track_id=track_id, artist_id=art.id)
            track_artists.append(t_art_obj)

            if crud.track_artist.get(db, track_id=track_id, artist_id=art.id):
                continue

            crud.track_artist.create(db, obj_in=t_art_obj)
            # logger.info(f"Track<>Artist pushed ({track_id}, {art.id})!")

    return track_artists


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_track_x_playlist(
    self, track_id: str, playlist_id: str
) -> schemas.TrackPlaylist:
    track_play = schemas.TrackPlaylist(track_id=track_id, playlist_id=playlist_id)

    with session_scope() as db:
        if not crud.track_playlist.get(db, track_id=track_id, playlist_id=playlist_id):
            crud.track_playlist.create(
                db, obj_in=track_play,
            )
            # logger.info(f"Track<>Playlist pushed ({track_id}, {playlist_id})!")

    return track_play


@celery_app.task(bind=True, task_time_limit=30, ignore_result=True, serializer="pickle")
def push_artist_x_genres(
    self, genres: Union[List[Dict[str, Any]], List[schemas.Genre]], artist_id: str
) -> List[schemas.GenreArtist]:
    artist_genres = []

    if genres:
        if isinstance(genres[0], dict):
            genres = parser.genre.from_genre_list(obj_in=genres)
    else:
        return artist_genres

    with session_scope() as db:
        for g in genres:
            art_genre_obj = schemas.GenreArtist(genre_id=g.id, artist_id=artist_id)
            artist_genres.append(art_genre_obj)

            if crud.genre_artist.get(db, genre_id=g.id, artist_id=artist_id):
                continue

            crud.genre_artist.create(
                db, obj_in=art_genre_obj,
            )
            # logger.info(f"Genre<>Artist pushed ({g.id}, {artist_id})!")

    return artist_genres

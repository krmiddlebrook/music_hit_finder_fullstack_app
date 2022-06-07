from typing import List, Optional, Dict, Any, Union

from fastapi.encoders import jsonable_encoder
from celery import chord, group, chain
from celery.utils.log import get_task_logger
from celery.result import AsyncResult
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.db.session import session_scope

from app import crud, schemas, models, push
from app.spotify import parser
from app.spotify.spapi import spapi
from app.spotify.spotify_mux import spotify_mux
from app.spotify import association


logger = get_task_logger(__name__)

# The ideal push artist will 1) fetch artist info (verified, active, name, discography, genres),
# 2) fetch artist insights (followers, monthly listeners, links, cities), and 3) push
# all data to the appropriate tables without making unnecessary db or api calls.

# TODO: finish flow for scrapping artist (cities and links)


# TODO: Make parser for artist stat, artist link, genre_artist, city,
# city_count, city_artist
@celery_app.task(bind=True, ignore_result=False, serializer="json")
def fetch_artist_info(self, artist_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve artist info (releases, listeners, name, verified, active, etc) from the
    SPAPI artist_info endpoint.
    """
    return {"info": spapi.artist_info(artist_id)}


@celery_app.task(bind=True, ignore_result=False, serializer="json")
def fetch_artist_insights(self, artist_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve artist insights (social links, cities, images, followers) from the SPAPI
    artist_insights endpoint.
    """
    return {"insights": spapi.artist_insights(artist_id)}


@celery_app.task(bind=True, ignore_result=False, serializer="json")
def fetch_artist_about(
    self, artist_id: str, spm_iter: int = 0, limit: int = 500
) -> List[Dict[str, Any]]:
    """
    Retrieve artist metadata (genres, id, name, followers) from the given artist's
    Spotify API artist endpoint.
    """
    return {"about": spotify_mux.artist_about(artist_id)}


@celery_app.task(
    bind=True,
    task_time_limit=2,
    ignore_result=False,
    serializer="json",
    queue="short-queue",
)
def parse_artist(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Parse artist schema object from the returned results from fetch_artist_info,
    fetch_artist_insight, and fetch_artist_about. Schema object is returned as a
    dict to make it serializable.
    """
    results = {k: v for d in results for k, v in d.items()}

    artist = parser.artist.from_dict(obj_in=results["about"])
    if results["insights"]:
        insights = parser.artist.from_dict(obj_in=results["insights"])
        artist.links = insights.links
    if results["info"]:
        info = parser.artist.from_dict(obj_in=results["info"])
        artist.verified = info.verified
        artist.active = info.active
        artist.related_artists = info.related_artists
        artist.releases = info.releases

    return jsonable_encoder(artist)


@celery_app.task(bind=True, task_time_limit=5, serializer="json")
def push_artist(
    self,
    artist: Union[Dict[str, Any], schemas.ArtistCreate],
    push_related_artists: Optional[bool] = True,
    push_discography: Optional[bool] = False,
) -> Dict[str, Any]:
    """
    Push artist to the db.
    """
    if isinstance(artist, dict):
        artist = parser.artist.from_dict(obj_in=artist)

    # TODO: handle artist cities, stats, images
    with session_scope() as db:
        db_art = crud.artist.get(db, id=artist.id)
        if not db_art:
            crud.artist.create(db, obj_in=artist)
            # logger.info(f"Artist pushed! ({artist.name}")
        else:
            if (db_art.verified is None and artist.verified is not None) or (
                db_art.active is None and artist.active is not None
            ):
                crud.artist.update_status(db, db_obj=db_art, new_info=artist)
                # logger.info(f"Artist status updated! ({artist.name}")
            elif (
                db_art.verified != artist.verified and artist.verified is not None
            ) or (db_art.active != artist.active and artist.active is not None):
                crud.artist.update_status(db, db_obj=db_art, new_info=artist)
                # logger.info(f"Artist status updated! ({artist.name}")
            if not db_art.genres and artist.genres:
                _ = crud.genre_artist.create_multi_from_artist_ids(
                    db, artist_ids=[artist.id], genres=[artist.genres]
                )
                # association.push_artist_x_genres(
                #     artist=jsonable_encoder(artist), ignore_result=True
                # )
                # crud.artist.update_genres(db, db_obj=db_art, genres=artist.genres)
                # logger.info(f"Artist genres updated! ({artist.name}")
            if not db_art.links and artist.links:
                _ = crud.artist_link.create_multi_from_artist_ids(
                    db, artist_ids=[artist.id], links=[artist.links]
                )
                # association.push_artist_x_links(
                #     artist=jsonable_encoder(artist), ignore_result=True
                # )
                # for link in artist.links:
                #     crud.artist_link.create(db, obj_in=link)
        if artist.related_artists and push_related_artists:
            for ra in artist.related_artists:
                if not crud.artist.get(db, id=ra.id):
                    # crud.artist.create(db, obj_in=ra)
                    # Set push_related_artists to false to avoid crawling spotify's
                    # entire library of artists just from one artist id lol.
                    flow_artist.si(
                        artist_id=ra.id,
                        check_db_first=False,
                        push_related_artists=False,
                        push_discography=True,
                    ).apply_async()
        if artist.releases and push_discography and artist.verified:
            push_artist_discography.si(artist=jsonable_encoder(artist)).apply_async()
        return jsonable_encoder(db_art)


@celery_app.task(bind=True, task_time_limit=10, ignore_result=True, serializer="json")
def push_artist_discography(
    self, artist: Union[Dict[str, Any], schemas.ArtistCreate],
) -> None:
    if isinstance(artist, dict):
        artist = parser.artist.from_dict(obj_in=artist)
    if not artist.releases:
        return

    singles = True
    get_albums = True
    albums = parser.album.from_releases(
        obj_in=artist.releases, singles=singles, albums=get_albums
    )
    tracks = parser.track.from_releases(
        obj_in=artist.releases, singles=singles, albums=get_albums
    )
    with session_scope() as db:
        # Push albums
        album_ids = [a.id for a in albums]
        missing_album_ids = set(crud.album.get_missing_ids_by_ids(db, ids=album_ids))
        missing_albums = []
        artist_ids = []
        for a in albums:
            if a.id in missing_album_ids:
                missing_albums.append(jsonable_encoder(a))
                artist_ids.append([artist.id])
        _ = crud.album.create_multi(db, objs_in=missing_albums, artist_ids=artist_ids)

        # Push tracks
        track_ids = [t.id for t in tracks]
        missing_track_ids = set(crud.track.get_missing_ids_by_ids(db, ids=track_ids))
        missing_tracks = []
        artist_ids = []
        for t in tracks:
            if t.id in missing_track_ids:
                missing_tracks.append(t)
                artist_ids.append([artist.id])
        _ = crud.track.create_multi(db, objs_in=missing_tracks)


@celery_app.task(bind=True, task_time_limit=6, ignore_result=True, serializer="json")
def flow_artist(
    self,
    artist_id: str,
    check_db_first: Optional[bool] = True,
    push_related_artists: Optional[bool] = True,
    push_discography: Optional[bool] = False,
) -> Any:
    """
    Workflow to fetch artist metadata and push it to the db.
    """
    if check_db_first:
        with session_scope() as db:
            db_artist = crud.artist.get(db, id=artist_id)
            if db_artist:
                if db_artist.verified is not None and db_artist.active is not None:
                    # Artist already in db
                    return
            else:
                push_discography = True

    workflow = (
        group(
            [
                fetch_artist_info.si(artist_id=artist_id),
                fetch_artist_insights.si(artist_id=artist_id),
                fetch_artist_about.si(artist_id=artist_id),
            ]
        )
        | parse_artist.s()
        | push_artist.s(
            push_related_artists=push_related_artists, push_discography=push_discography
        )
    )
    workflow.apply_async(ignore_result=True)
    # return workflow()

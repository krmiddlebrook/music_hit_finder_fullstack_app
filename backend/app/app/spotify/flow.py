from typing import List, Optional, Dict, Any, Union
import datetime
import random
import time
import shutil

from celery import chord, group, chain
from celery.utils.log import get_task_logger
from celery.result import ResultBase

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import session_scope

from app import crud, schemas, push
from app.spotify import parser
from app.spotify.spotify_mux import spotify_mux
from app.spotify import utils

from app.spotify import artist
from app.spotify import track
from app.spotify import album
from app.spotify import track_playcount
from app.spotify import association
from app.spotify import genre
from app.spotify import playlist_track
from app.spotify import spectrogram
from app.spotify import track_prediction
from app.spotify import track_distance

logger = get_task_logger(__name__)

# TODO: finish flow for scrapping artist (cities and links)


@celery_app.task(bind=True, serializer="json")
def flow_update_tracks(self, skip: int = 0, limit: int = 100_000) -> int:
    """
    Update track metadata with Spotify api data for tracks in our db.

    The flow performs the following steps:
        get track ids missing preview urls
        chunck tracks into sets of 50 track ids
        for each chunk of track ids:
            for each track:
                push updated track to db
    repeat: 1/week
    """
    with session_scope() as db:
        track_ids = [
            t.id
            for t in crud.track.get_tracks_missing_preview_url(
                db, skip=skip, limit=limit
            )
        ]

    chunked_ids = utils.chunkify(track_ids, chunk_size=50)
    logger.info(
        f"Collecting additional metadata for {len(chunked_ids)} sets of track ids!"
    )

    for ids in chunked_ids:
        # Send request to Spotify API for tracks metadata
        # Process metadata and push results to db
        time.sleep(0.1)  # avoid flooding spotify api with requests
        track.flow_tracks(track_ids=ids)

    total_tasks = len(chunked_ids)
    return total_tasks


@celery_app.task(bind=True, serializer="json")
def flow_update_artists(self, skip: int = 0, limit: int = 100_000) -> int:
    """
    Update artist metadata with Spotify API data for artists in our db.

    The flow performs the following steps:
        get artist ids missing links or genres
        for each artist:
            push artist to db
    repeat: 1/week
    """
    with session_scope() as db:
        artist_ids = [
            a.id
            for a in crud.artist.get_artist_ids_missing_data(db, skip=skip, limit=limit)
        ]

    logger.info(f"Updating metadata for {len(artist_ids)} artists!")
    for aid in artist_ids:
        # Send request to Spotify API for tracks metadata
        # Process metadata and push results to db
        time.sleep(0.1)  # avoid flooding spotify api with requests
        artist.flow_artist.si(
            artist_id=aid,
            check_db_first=False,
            push_related_artists=True,
            push_discography=True,
        ).apply_async(ignore_result=True)

    total_tasks = len(artist_ids)
    return total_tasks


@celery_app.task(bind=True, serializer="json")
def flow_update_albums(self, skip: int = 0, limit: int = 100_000) -> None:
    """
    Update album metadata with Spotify Client data for albums in our db.

    The flow performs the following steps:
        get album ids missing metadata in our db (cover image, label_id, etc.)
        for each album:
            push updated album to db
    repeat: 1/week
    """
    with session_scope() as db:
        album_ids = [
            a.id
            for a in crud.album.get_album_ids_by_verified_artists_missing_data(
                db,
                min_date=datetime.date.today() - datetime.timedelta(days=int(365 * 2)),
                max_date=datetime.date.today(),
                skip=skip,
                limit=limit,
            )
        ]

    logger.info(f"Updating metadata for {len(album_ids)} albums!")

    # TODO: batch update albums using spotify api result for multi albums
    for aid in album_ids:
        # Send request to Spotify Client API for album metadata
        # Process metadata and push results to db
        # time.sleep(0.1)  # avoid flooding spotify client api with requests
        album.flow_update_album.si(album_id=aid).apply_async()


@celery_app.task(bind=True, serializer="json")
def flow_scrape_playlists_tracks(
    self, playlist_tracks_limit: int = 300, skip: int = 0, limit: int = 2_000,
) -> None:
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
            p.id for p in crud.playlist.get_popular_playlists(db, skip=0, limit=limit)
        ]

    logger.info(f"Collecting tracks for {len(playlists_ids)} playlist!")
    # tasks = []
    for play_id in playlists_ids:
        playlist_track.flow_playlist_tracks(
            playlist_id=play_id, track_limit=playlist_tracks_limit
        )


@celery_app.task(bind=True)
def flow_scrape_album_playcounts(
    self,
    min_release_date: datetime.date = datetime.date.today()
    - datetime.timedelta(days=int(365 * 2)),
    max_release_date: datetime.date = datetime.date.today(),
    verified_artists: Optional[bool] = True,
    skip: Optional[int] = 0,
    limit: Optional[int] = 100_000,
) -> int:
    """
    Collect album track playcounts.

    The flow performs the following steps:
        get album ids (only include albums by verified artists)
        for each album id:
            get tracks playcounts
        for each track:
            chain(
                push_track (if necessary),
                push_track_playcount
            )
    repeat: 3/week
    """
    with session_scope() as db:
        album_ids = [
            a.id
            for a in crud.album.get_ids_missing_playcount(
                db,
                min_release_date=min_release_date,
                max_release_date=max_release_date,
                verified_artists=verified_artists,
                skip=skip,
                limit=limit,
            )
        ]

    logger.info(f"Collecting album playcounts for {len(album_ids)} ")
    for album_id in album_ids:
        time.sleep(0.05)  # small jitter between tasks
        track_playcount.flow_album_playcount(album_id=album_id)

    total_tasks = len(album_ids)
    return total_tasks


# TODO: flow for spectrogram, track predictions, artist disco/links, album playcounts
@celery_app.task(bind=True)
def flow_scrape_spectrograms(
    self,
    rising_tracks_only: Optional[bool] = True,
    lag_days: Optional[int] = 30,
    skip: Optional[int] = 0,
    limit: Optional[int] = 1_000,
) -> int:
    """
    Collect spectrograms for tracks.

    The flow performs the following steps:
        get track ids (only include rising tracks by verified artists and with
        preview_urls)
        for each track:
            chain(
                download spectrogram (if necessary),
                push spectrogram
            )

    repeat: 2/week
    """
    remake_audio_dir = True
    if settings.AUDIO_DIR.exists() and remake_audio_dir:
        shutil.rmtree(settings.AUDIO_DIR)
    settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    settings.MP3_DIR.mkdir(parents=True, exist_ok=True)
    settings.WAV_DIR.mkdir(parents=True, exist_ok=True)

    with session_scope() as db:
        if rising_tracks_only:
            tracks = [
                (t.id, t.preview_url)
                for t in crud.track.get_rising_tracks_missing_spectrograms(
                    db,
                    lag_days=lag_days,
                    order_by="growth_rate",
                    skip=skip,
                    limit=limit,
                )
            ]
        else:
            tracks = [
                (t.id, t.preview_url)
                for t in crud.track.get_tracks_missing_spectrograms(
                    db, lag_days=lag_days, skip=skip, limit=limit
                )
            ]

    logger.info(f"Collecting spectrograms for {len(tracks)} tracks.")
    for tid, preview_url in tracks:
        spectrogram.flow_spectrogram.si(
            track_id=tid, preview_url=preview_url
        ).apply_async()

    total_tasks = len(tracks)
    return total_tasks


@celery_app.task(bind=True)
def flow_track_predictions(
    self,
    model_id: str = settings.MODEL_ID,
    rising_tracks_only: Optional[bool] = True,
    lag_days: int = 30,
    skip: int = 0,
    limit: int = 20_000,
) -> int:
    """
    Generate track predictions for tracks.

    The flow performs the following steps:
        get track ids (that are mising predictions)
        chunk track_ids list to max batch size of model
        for each track_ids chunk:
            get spectrograms
            generate predictions
            push track_id <> prediction to db


    repeat: 3/week and/or as needed
    """
    with session_scope() as db:
        if rising_tracks_only:
            track_ids = [
                t.id
                for t in crud.track.get_rising_tracks_to_predict(
                    db, lag_days=lag_days, skip=skip, limit=limit
                )
            ]
        else:
            track_ids = [
                t.id
                for t in crud.track.get_tracks_missing_predictions(
                    db, lag_days=lag_days, skip=skip, limit=limit
                )
            ]

    # Chunk track_ids
    total_tracks = len(track_ids)
    track_ids = utils.chunkify(track_ids, chunk_size=settings.MAX_BATCH_SIZE)

    logger.info(f"Created {len(track_ids)} tasks to generate track predictions!")
    # TODO: bulk insert/update track preds
    for tids in track_ids:
        track_prediction.predict_tracks.si(
            track_ids=tids, model_id=model_id
        ).apply_async(ignore_result=True)

    return total_tracks


@celery_app.task(bind=True, queue="distance-queue")
def flow_track_distances(
    self,
    spotify_ids: Optional[Union[List[str], str]] = None,
    user_limit: int = 1e7,
    user_skip: int = 0,
    lag_period: int = 30,
    days_since_release: int = 180,
    canidate_hit_limit: int = 2_000,
    limit: int = 50_000,
    skip: int = 0,
) -> int:
    """
    Compute track distances for track pairs missing a distance.

    The flow performs the following steps:
        get track ids (that are missing)
        chunk track_ids list to max batch size of model
        for each track_ids chunk:
            get spectrograms
            generate predictions
            push track_id <> prediction to db


    repeat: 3/week and/or as needed
    """
    # Get canidate hit <> user track distance pairs.
    with session_scope() as db:
        # spotify_ids = [u.spotify_id for u in crud.user.get_users_with_spotify_id(db)]
        td_canidate_pairs = crud.user.get_canidate_track_pairs_by_users(
            db,
            spotify_ids=spotify_ids,
            user_limit=user_limit,
            user_skip=user_skip,
            lag_period=lag_period,
            days_since_release=days_since_release,
            canidate_hit_limit=canidate_hit_limit,
            limit=limit,
            skip=0,
        )
    print("~" * 100)
    print(
        f"Calculating distance for {len(td_canidate_pairs)} User <> Hit Canidate Pairs."
    )
    print("~" * 100)
    print("\n")

    # Compute canidate hit <> user track distances and push to db.
    chunked_pairs = utils.chunkify(
        td_canidate_pairs, chunk_size=settings.MAX_BATCH_SIZE
    )
    for pairs in chunked_pairs:
        track_distance.flow_tracks_distances.si(track_ids=pairs).apply_async(
            ignore_result=True
        )

    return len(td_canidate_pairs)


@celery_app.task(bind=True)
def flow_refresh_materialized_views(self) -> List[str]:
    """
    Refresh all materialized views in the db and return a list with their
    names.
    """
    # TODO: create object with list of materialized views
    with session_scope() as db:
        refreshed_mv_list = crud.materialized_view.refresh_all(db)
        return refreshed_mv_list

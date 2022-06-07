from typing import Any, List, Dict
import time
import itertools
import random
import requests
import datetime

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import text
from celery import group
from celery.result import ResultBase

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils import send_new_account_email
from app import spotify

router = APIRouter()


@router.get("/", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users.
    """
    users = crud.user.get_multi(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=schemas.User)
def create_user_from_admin(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new user if current user has admin privileges.
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud.user.create(db, obj_in=user_in)
    if settings.EMAILS_ENABLED and user_in.email:
        send_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
    return user


@router.post("/create", response_model=schemas.User)
def create_user(
    *, db: Session = Depends(deps.get_db), user_in: schemas.UserCreate,
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    if not settings.USERS_OPEN_REGISTRATION:
        raise HTTPException(
            status_code=403,
            detail="Open user registration is forbidden on this server",
        )
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system",
        )
    user = crud.user.create(db, obj_in=user_in)
    if settings.EMAILS_ENABLED and user_in.email:
        send_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
    return user


@router.put("/me", response_model=schemas.User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    password: str = Body(None),
    full_name: str = Body(None),
    email: EmailStr = Body(None),
    spotify_id: str = Body(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    current_user_data = jsonable_encoder(current_user)
    user_in = schemas.UserUpdate(**current_user_data)
    if password is not None:
        user_in.password = password
    if full_name is not None:
        user_in.full_name = full_name
    if email is not None:
        user_in.email = email
    if spotify_id is not None:
        user_in.spotify_id = spotify_id

    user = crud.user.update(db, db_obj=current_user, obj_in=user_in)
    return user


@router.get("/me", response_model=schemas.User)
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = crud.user.get(db, id=user_id)
    if user == current_user:
        return user
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return user


@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a user.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    user = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user


@router.post("/me/playlist", response_model=schemas.UserPlaylist)
def create_user_playlist(
    *,
    db: Session = Depends(deps.get_db),
    top_artists: List[Dict[str, Any]],
    top_tracks: List[Dict[str, Any]],
    spotify_token: str = Body(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a playlist for the current user.
    """
    lag_period = 30
    days_since_release = 180
    canidate_hit_limit = 3_000
    conn_timeout, read_timeout = 3, 10
    if not current_user.spotify_id:
        raise HTTPException(
            status_code=400, detail="The user must login to Spotify first"
        )
    # 1. Push user tracks to track_user table
    # 2. Collect spectrograms for user tracks
    # 3. Calculate track distances between user track hit track pairs
    # 4. Get canidate hit tracks (hit tracks with the smallest distance aren't in the user's library)

    # Get recommended track ids
    rec_track_ids = [
        f'spotify:track:{rec["id"]}'
        for rec in crud.user.get_track_recs_for_user(
            db,
            spotify_id=current_user.spotify_id,
            lag_period=lag_period,
            days_since_release=days_since_release,
            limit=40,
            skip=0,
        )
    ]
    print("~" * 100)
    print(f"User Playlist Track Recommendations: {len(rec_track_ids)}")
    print("~" * 100)
    print("\n")
    musicai_playlist = crud.musicai_playlist.get_by_user(
        db, spotify_user_id=current_user.spotify_id
    )
    if not musicai_playlist:
        print("~" * 100)
        print(f"Current User: {jsonable_encoder(current_user)}")
        print("~" * 100)
        print("\n")
        description = (
            "A playlist created just for you of the hottest new music "
            "(updated weekly). Enjoy! - more @ musicai.io"
        )
        resp = requests.post(
            f"https://api.spotify.com/v1/users/{current_user.spotify_id}/playlists",  # noqa: E501
            headers={
                "Authorization": f"Bearer {spotify_token}",
                "Content-Type": "application/json",
            },
            json=dict(name="Your MusicAI Mix", description=description,),
            timeout=(conn_timeout, read_timeout),
        ).json()

        print("~" * 100)
        print(f"Playlist Creation response:\n {resp} \n")
        print("~" * 100)
        print("\n")
        playlist_id = resp["id"]
        url = resp["external_urls"]["spotify"]

        playlist_obj = schemas.PlaylistCreate(
            id=playlist_id,
            owner_id=current_user.spotify_id,
            name=resp.get("name", None),
        )
        _ = crud.playlist.create(db, obj_in=playlist_obj)

        musicai_playlist_obj = schemas.MusicaiPlaylistCreate(
            playlist_id=playlist_id, owner_id=current_user.spotify_id, playlist_url=url,
        )
        musicai_playlist = crud.musicai_playlist.create(db, obj_in=musicai_playlist_obj)

    if len(rec_track_ids) >= 40:
        requests.put(
            f"https://api.spotify.com/v1/playlists/{musicai_playlist.playlist_id}/tracks",  # noqa: E501
            headers={
                "Authorization": f"Bearer {spotify_token}",
                "Content-Type": "application/json",
            },
            json=dict(uris=rec_track_ids,),
            timeout=(conn_timeout, read_timeout),
        )
        # TODO: add rec tracks to track_playlist association table.
        musicai_playlist = crud.musicai_playlist.update(db, db_obj=musicai_playlist)
        playlist_tracks = spotify.spotify_mux.spotify_mux.playlist_tracks(
            musicai_playlist.playlist_id, token=spotify_token
        )

        user_playlist = schemas.UserPlaylist(
            user_id=current_user.id,
            tracks=playlist_tracks,
            playlist_id=musicai_playlist.playlist_id,
            playlist_url=musicai_playlist.playlist_url,
        )
        spotify.spotify_user.update_user_canidate_tracks(
            spotify_id=current_user.spotify_id,
            tracks=top_tracks,
            top_track=True,
            source="top-tracks",
            lag_period=lag_period,
            days_since_release=days_since_release,
            canidate_hit_limit=canidate_hit_limit,
            skip=0,
            wait_until_complete=False,
        )
        return user_playlist

    # If we don't have enough data on the user to generate a playlist, run this flow.
    # WARNING: this process can take up to 10 minutes to return a playlist to the user.
    # 1. Push user tracks to track_user table
    # 2. Collect spectrograms for user tracks
    # 3. Calculate track distances between user track hit track pairs
    # 4. Get canidate hit tracks (hit tracks with the smallest distance that aren't in the user's library)
    pushed_user_tracks = spotify.spotify_user.update_user_canidate_tracks(
        current_user.spotify_id,
        tracks=top_tracks,
        top_track=True,
        source="top-tracks",
        wait_until_complete=True,
    )
    print("~" * 100)
    print(f"PUSHED USER TRACKS: {len(pushed_user_tracks)}")
    print("~" * 100)
    print("\n")

    # Get recommended track ids
    rec_track_ids = [
        f'spotify:track:{rec["id"]}'
        for rec in crud.user.get_track_recs_for_user(
            db,
            spotify_id=current_user.spotify_id,
            lag_period=lag_period,
            days_since_release=days_since_release,
            limit=40,
            skip=0,
        )
    ]
    print("User Playlist Track Recommendations!")
    print("~" * 50)
    print(len(rec_track_ids))
    print()

    print("~" * 100)
    print(f"Current User: {jsonable_encoder(current_user)}")
    print("~" * 100)
    print("\n")

    requests.post(
        f"https://api.spotify.com/v1/playlists/{musicai_playlist.playlist_id}/tracks",  # noqa: E501
        headers={
            "Authorization": f"Bearer {spotify_token}",
            "Content-Type": "application/json",
        },
        json=dict(uris=rec_track_ids,),
        timeout=(conn_timeout, read_timeout),
    )
    musicai_playlist = crud.musicai_playlist.update(db, db_obj=musicai_playlist)
    playlist_tracks = spotify.spotify_mux.spotify_mux.playlist_tracks(
        musicai_playlist.playlist_id, token=spotify_token
    )
    user_playlist = schemas.UserPlaylist(
        user_id=current_user.id,
        tracks=playlist_tracks,
        playlist_id=musicai_playlist.playlist_id,
        playlist_url=musicai_playlist.playlist_url,
    )
    return user_playlist

from typing import Any, List
import datetime

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils import send_new_account_email

router = APIRouter()


@router.get("/", response_model=List[schemas.Track])
def read_tracks(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve tracks.
    """
    tracks = crud.track.get_multi(db, skip=skip, limit=limit)
    return tracks


@router.get("/rising-tracks", response_model=List[schemas.TrackRising])
def read_rising_tracks(
    db: Session = Depends(deps.get_db),
    lag_days: int = 7,
    order_by: str = "musicai_score",
    min_growth_rate: float = 0,
    max_growth_rate: float = 1e9,
    min_playcount: int = 0,
    max_playcount: int = 1e10,
    min_chg: float = 0,
    max_chg: float = 1e9,
    min_probability: float = 0.0,
    max_probability: float = 1.0,
    min_musicai_score: int = 1,
    max_musicai_score: int = 5,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve rising tracks.
    """
    # TODO: Make order_by an enum or set.

    tracks_rising_base = {
        t.id: t
        for t in crud.track.get_rising_tracks(
            db,
            lag_days=lag_days,
            order_by=order_by,
            min_growth_rate=min_growth_rate,
            max_growth_rate=max_growth_rate,
            min_playcount=min_playcount,
            max_playcount=max_playcount,
            min_chg=min_chg,
            max_chg=max_chg,
            min_probability=min_probability,
            max_probability=max_probability,
            min_musicai_score=min_musicai_score,
            max_musicai_score=max_musicai_score,
            skip=skip,
            limit=limit,
        )
    }

    tracks = {
        t.id: t
        for t in crud.track.get_tracks(db, track_ids=list(tracks_rising_base.keys()))
    }

    if len(tracks) != len(tracks_rising_base):
        raise HTTPException(
            status_code=400,
            detail="Track rising base and tracks must be the same length!",
        )

    tracks_rising = []
    for tid in tracks_rising_base.keys():
        rising_base = tracks_rising_base[tid]
        track = tracks[tid]
        days_since_release = (datetime.date.today() - track.album.release_date).days
        track_rising = schemas.TrackRising(
            **rising_base.dict(),
            track=track,
            artists=track.artists,
            album=track.album,
            days_since_release=days_since_release
        )
        tracks_rising.append(track_rising)

    # tracks_rising = sorted(tracks_rising, key=lambda t: t.growth_rate, reverse=True)

    return tracks_rising


@router.get("/me", response_model=schemas.User)
def read_user_me_tracks(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user's tracks.
    """
    return current_user

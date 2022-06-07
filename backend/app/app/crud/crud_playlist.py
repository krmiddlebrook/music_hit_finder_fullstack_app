from typing import List

from sqlalchemy import text, Integer, String
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.playlist import Playlist
from app.schemas.playlist import PlaylistCreate, PlaylistUpdate
from app.spotify.config import INFLUENTIAL_PLAYLIST_THRESH


class CRUDPlaylist(CRUDBase[Playlist, PlaylistCreate, PlaylistUpdate]):
    # TODO: functions to retrieve playlist by owner and by name
    def get_popular_playlists(
        self,
        db: Session,
        min_followers: int = INFLUENTIAL_PLAYLIST_THRESH,
        *,
        skip: int = 0,
        limit: int = 1_000,
    ) -> List[Playlist]:
        # TODO: define the term_ids to exclude in a config file
        stmt = """
            with pf as (
                select p.id id,
                    max(pfc.followers_count) followers_count
                from playlist p
                join playlist_followers_count pfc on pfc.playlist_id = p.id
                where pfc.followers_count >= :min_followers
                group by p.id
                order by max(pfc.followers_count) desc
            ), fp as (
                select *
                from pf
                join term_playlist tp on tp.playlist_id = pf.id
                where term_id not in (
                        'Ambient',
                        'Cumbia',
                        'lofi',
                        'Kayōkyoku',
                        'Indian Classical',
                        'War metal',
                        'Celtic'
                        'Happy hardcore'
                        'Doom metal'
                    )
            ) select fp.id id
            from fp
            group by fp.id
            order by max(followers_count) desc
            limit :limit offset :skip
        """
        stmt = (
            text(stmt)
            .bindparams(min_followers=min_followers, limit=limit, skip=skip,)
            .columns(id=String)
        )
        return db.execute(stmt).fetchall()

    def get_by_spotify_user(
        self, db: Session, *, spotify_user_id: str, skip: int = 0, limit: int = 1_000,
    ) -> List[Playlist]:
        result = (
            db.query(Playlist)
            .filter(Playlist.owner_id == spotify_user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        if not result:
            result = []
        return result


playlist = CRUDPlaylist(Playlist)

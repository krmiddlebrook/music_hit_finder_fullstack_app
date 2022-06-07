from typing import Optional, List
from collections import defaultdict

from sqlalchemy.orm import Session
from celery.utils.log import get_task_logger

from app.crud.base import CRUDBase
from app.models.genre_artist import Genre_Artist
from app.schemas.genre_artist import GenreArtistCreate, GenreArtistUpdate
from app.schemas.genre import Genre
from .crud_genre import genre

logger = get_task_logger(__name__)


class CRUDGenreArtist(CRUDBase[Genre_Artist, GenreArtistCreate, GenreArtistUpdate]):
    def create(self, db: Session, *, genre_id: str, artist_id: str) -> Genre_Artist:
        # Push genre if necessary
        if not genre.get(db, id=genre_id):
            db_genre = genre.create(db, obj_in=Genre(id=genre_id))

        obj_in = GenreArtistCreate(genre_id=genre_id, artist_id=artist_id)
        return super().create(db, obj_in=obj_in, refresh=False)

    def create_multi_from_artist_ids(
        self, db: Session, *, artist_ids: List[str], genres: List[List[Genre]]
    ) -> bool:
        """
        Create artist_id <> genre_id pairs for each artist in the artist_ids list.
        `genres` is a list of lists, where each sublist contains a set of
        genre ids to be paired with the artist_id from the same index in the
        artist_ids list.
        """

        db_pairs = defaultdict(set)
        for db_ga in (
            db.query(Genre_Artist).filter(Genre_Artist.artist_id.in_(artist_ids)).all()
        ):
            db_pairs[db_ga.artist_id].add(db_ga.genre_id)

        canidate_pairs = []
        canidate_genres = {}
        for aid, gobjs in zip(artist_ids, genres):
            for gobj in gobjs:
                if gobj.id not in db_pairs[aid]:
                    canidate_pairs.append(
                        GenreArtistCreate(artist_id=aid, genre_id=gobj.id).dict()
                    )
                    canidate_genres[gobj.id] = gobj

        # Push genres if necessary
        missing_genre_ids = set(
            genre.get_missing_ids_by_ids(db, ids=list(canidate_genres.keys()))
        )
        missing_genres = [
            g.dict() for gid, g in canidate_genres.items() if gid in missing_genre_ids
        ]
        _ = genre.create_multi(db, objs_in=missing_genres)
        # Push artist <> genre pairs
        return super().create_multi(db, objs_in=canidate_pairs)

    def get(
        self, db: Session, *, genre_id: str, artist_id: str
    ) -> Optional[Genre_Artist]:
        return (
            db.query(Genre_Artist)
            .filter(
                Genre_Artist.genre_id == genre_id, Genre_Artist.artist_id == artist_id
            )
            .first()
        )


genre_artist = CRUDGenreArtist(Genre_Artist)

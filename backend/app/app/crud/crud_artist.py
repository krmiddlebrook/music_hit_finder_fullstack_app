from typing import Any, Dict, Optional, List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import text, String
from sqlalchemy.exc import IntegrityError
from celery.utils.log import get_task_logger

from app.crud.base import CRUDBase
from app.models.artist import Artist
from app.models.genre_artist import Genre_Artist
from app.schemas.artist import ArtistCreate, ArtistUpdate
from app.schemas.genre import Genre
from app.schemas.artist_link import ArtistLink

from .crud_genre import genre
from .crud_genre_artist import genre_artist
from .crud_artist_link import artist_link

from app.spotify.spapi import spapi
from app.spotify import parser
from app.spotify import association

logger = get_task_logger(__name__)


class CRUDArtist(CRUDBase[Artist, ArtistCreate, ArtistUpdate]):
    def create(self, db: Session, *, obj_in: ArtistCreate) -> Artist:
        # push artist -> push artist genres
        # artist_data = jsonable_encoder(obj_in)
        # genres_data = artist_data.pop("genres", [])
        # links_data = artist_data.pop("links", [])

        db_artist = Artist(
            id=obj_in.id,
            name=obj_in.name,
            verified=obj_in.verified,
            active=obj_in.active,
        )
        try:
            # Add the db_artist to db
            db.add(db_artist)
            db.commit()
            # db.refresh(db_artist)
            # logger.info(f"Artist created ({db_artist.id}, {db_artist.name})!")
        except IntegrityError as integ_err:  # noqa: F841
            logger.warning(f"Unique constraint violated for {Artist.__tablename__}")
            db.rollback()
        except Exception as err:  # noqa: F841
            logger.warning(f"ERROR Inserting to {Artist.__tablename__} \n {err}")
            db.rollback()

        # Add artist <> link to db
        # association.push_artist_x_links(artist=jsonable_encoder(obj_in))
        _ = artist_link.create_multi_from_artist_ids(
            db, artist_ids=[obj_in.id], links=[obj_in.links]
        )
        # Add artist <> genre associations to db
        if obj_in.genres:
            # Push genres and artist <> genre associations
            _ = genre_artist.create_multi_from_artist_ids(
                db, artist_ids=[obj_in.id], genres=[obj_in.genres]
            )
        # association.push_artist_x_genres(artist=jsonable_encoder(obj_in))
        return db_artist

    def update_status(
        self, db: Session, *, db_obj: Artist, new_info: ArtistCreate
    ) -> Artist:
        """
        Update artist's verified and/or active status.
        """
        if new_info.verified is not None:
            db_obj.verified = new_info.verified

        if new_info.active is not None:
            db_obj.active = new_info.active

        db.commit()
        # db.refresh(db_obj)
        return db_obj

    def update_genres(self, db: Session, db_obj: Artist, genres: List[Genre]) -> Artist:
        for g in genres:
            db_genre = genre.get(db, id=g.id)
            if not db_genre:
                db_genre = genre.create(db, obj_in=g)
                # print(f"Genre created! {db_genre.id}")

            db_genre_artist = genre_artist.get(
                db, genre_id=db_genre.id, artist_id=db_obj.id
            )
            if not db_genre_artist:
                db_genre_artist = genre_artist.create(
                    db, genre_id=db_genre.id, artist_id=db_obj.id
                )

        db.commit()
        # db.refresh(db_obj)
        return db_obj

    def get_artist_ids_missing_data(
        self, db: Session, *, skip: int = 0, limit: int = 10_000
    ) -> List[Any]:
        """
        Retrieve a list of artist ids that are missing data in the db. This includes
        artists that do not have information for links, genres, verified, or active.
        """
        stmt = """
            select a.id id
            from artist a
            left join artist_link al on al.artist_id = a.id
            left join genre_artist ga on ga.artist_id = a.id
            join album_artist aa on aa.artist_id = a.id
            join album alb on alb.id = aa.album_id
            where (al.link is null and ga.genre_id is null)
                or (a.verified is null or a.active is null)
            group by a.id
            order by max(alb.release_date) desc
            limit :limit offset :skip;
        """
        stmt = text(stmt).bindparams(limit=limit, skip=skip,).columns(id=String)
        return db.execute(stmt).fetchall()


artist = CRUDArtist(Artist)

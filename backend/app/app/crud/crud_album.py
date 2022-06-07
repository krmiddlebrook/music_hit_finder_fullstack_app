from typing import Optional, List, Any, Union, Dict
from datetime import date

from fastapi.encoders import jsonable_encoder
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc, String, text

from app.crud.base import CRUDBase
from app.models.album import Album
from app.schemas.album import AlbumCreate, AlbumUpdate
from app.schemas.label import Label
from app.models.album_artist import Album_Artist
from app.models.artist import Artist
from app.schemas.artist import ArtistCreate
from app.schemas.track import TrackCreate
from app.schemas.track_playcount import TrackPlaycount

from .crud_label import label
from .crud_album_artist import album_artist

from app import push
from app.push.push_track import track


logger = get_task_logger(__name__)


class CRUDAlbum(CRUDBase[Album, AlbumCreate, AlbumUpdate]):
    def create(
        self,
        db: Session,
        *,
        obj_in: AlbumCreate,
        artist_ids: Optional[List[str]] = None,
    ) -> Album:
        # push album artists -> push album label -> push album ->
        # push album <> artists associations -> push tracks -> push track playcounts
        # Add label to db if necessary
        if obj_in.label_id:
            label_obj = Label(id=obj_in.label_id)
            db_label = label.get(db, id=label_obj.id)
            if not db_label:
                db_label = label.create(db, obj_in=label_obj)
                # logger.info(f"Label created! ({db_label.id}, {db_label.name})")
        db_album = super().create(db, obj_in=obj_in, refresh=False)

        # Push album <> artist associations (we assume that the artists are already in
        # the artist table).
        if artist_ids:
            _ = album_artist.create_multi_from_album_ids(
                db, album_ids=[obj_in.album_id], artist_ids=[artist_ids]
            )

        # Push album tracks to db
        # for t in tracks:
        #     track.push_track(db, track=t)

        # Push track playcounts to db
        # for tp in tracks_playcounts:
        #     push.track.push_track_playcount(db, track_playcount=tp)
        return db_album

    def create_multi(
        self,
        db: Session,
        *,
        objs_in: List[Union[AlbumCreate, Dict[str, Any]]],
        artist_ids: Optional[List[List[str]]] = None,
    ) -> bool:
        """
        A convenience function to safely bulk insert a list or albums into the
        appropriate db table.
        """
        if len(objs_in) == 0:
            # Do nothing if there are no entries in the objs_in list/dict.
            return True
        if not isinstance(objs_in[0], dict):
            # Convert the list of CreateSchemaType to dict b/c that's the format sql
            # expects.
            objs_in = [obj.dict() for obj in objs_in]

        # Push labels to db
        label_objs = []
        label_ids = set()
        for al in objs_in:
            if al.get("label_id", None):
                if al["label_id"] not in label_ids:
                    label_objs.append(Label(id=al["label_id"]))
                    label_ids.add(al["label_id"])
        missing_label_ids = label.get_missing_ids_by_ids(db, ids=list(label_ids))
        missing_labels = [
            jsonable_encoder(l_obj)
            for l_obj in label_objs
            if l_obj.id in missing_label_ids
        ]
        _ = label.create_multi(db, objs_in=missing_labels)

        # Push albums
        push_successful = super().create_multi(db, objs_in=objs_in)

        # Push album<>artist associations (we assume that the artists are already in the
        # artist table)
        album_ids = [al["id"] for al in objs_in]
        if artist_ids:
            _ = album_artist.create_multi_from_album_ids(
                db, album_ids=album_ids, artist_ids=artist_ids
            )
        return push_successful

    def update(
        self, db: Session, *, db_obj: Album, obj_in: Union[AlbumUpdate, Dict[str, Any]],
    ) -> Album:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        # Add label to db and label id to album
        if update_data.get("label_id", None):
            label_obj = Label(id=update_data["label_id"])
            db_label = label.get(db, id=label_obj.id)
            if not db_label:
                db_label = label.create(db, obj_in=label_obj)
                # logger.info(f"Label created! ({db_label.id}, {db_label.name})")
            update_data["label_id"] = db_label.id

        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def get_ids_missing_playcount(
        self,
        db: Session,
        *,
        min_release_date: date,
        max_release_date: date = date.today(),
        verified_artists: bool = True,
        skip: int = 0,
        limit: int = 10_000,
    ) -> List[Any]:
        """
        Retrieve unique album ids missing track playcounts for the current date.
        """
        stmt = """
            with track_plays_today as (
                select track_id
                from track_playcount tp
                where tp.date = CURRENT_DATE
                group by track_id
            ) select
                al.id id
            from album al
            join track t on t.album_id = al.id
            left join track_plays_today tp on tp.track_id = t.id
            left join album_artist aa on aa.album_id = al.id
            left join track_artist ta on ta.track_id = t.id
            join artist a
                on a.id = ta.artist_id
                or a.id = aa.artist_id
            left join genre_artist ga on ga.artist_id = a.id
            where tp.track_id is null
                and al.release_date BETWEEN :min_release_date and :max_release_date
                and a.verified = :verified_artists
                and (
                    ga.genre_id not in (
                        'meditation',
                        'musica de fondo',
                        'pianissimo',
                        'world meditation',
                        'sleep',
                        'background piano',
                        'spa',
                        'atmosphere',
                        'musica para ninos',
                        'focus beats',
                        'lo-fi beats'
                    )
                    or ga.genre_id is null
                )
            group by al.id
            order by max(al.release_date) desc
            limit :limit offset :skip
        """
        stmt = (
            text(stmt)
            .bindparams(
                min_release_date=min_release_date.strftime("%Y-%m-%d"),
                max_release_date=max_release_date.strftime("%Y-%m-%d"),
                verified_artists=verified_artists,
                limit=limit,
                skip=skip,
            )
            .columns(id=String)
        )
        return db.execute(stmt).fetchall()

    def get_album_ids_by_verified_artists_missing_data(
        self,
        db: Session,
        *,
        min_date: date,
        max_date: Optional[date] = date.today(),
        skip: int = 0,
        limit: int = 10_000,
    ) -> List[Any]:
        """
        Retrieve unique album ids by verified artists that don't have any blacklisted
        genres but are missing album metadata (i.e., cover image, label_id, etc.).
        """
        # TODO: move this function to crud_track_playcount.
        stmt = """
            with verified_artists as (
                select a.id artist_id,
                    a.name artist_name,
                    a.verified,
                    a.active,
                    aa.album_id,
                    al.name album_name,
                    al.release_date,
                    al.total_tracks,
                    ga.genre_id
                from artist a
                join album_artist aa on aa.artist_id = a.id
                join album al on al.id = aa.album_id
                join genre_artist ga on ga.artist_id = a.id
                where a.verified = true
                    and al.release_date <= :max_date
                    and al.release_date >= :min_date
                    and al.total_tracks <= 32
                    and (al.cover is null or al.label_id is null)
                    and ga.genre_id not in (
                        'meditation',
                        'musica de fondo',
                        'pianissimo',
                        'world meditation',
                        'sleep',
                        'background piano',
                        'spa',
                        'background',
                        'atmosphere',
                        'musica para ninos',
                        'focus beats',
                        'lo-fi beats'
                    )
                order by al.release_date desc, al.total_tracks desc
            ), exlude_track_ids as (
                select tp.track_id,
                    max(tp.date) "date",
                    max(tp.playcount) playcount,
                    max(tp.popularity) popularity
                from track_playcount tp
                where tp.date = CURRENT_DATE
                group by tp.track_id
            ) select va.album_id id
            from verified_artists va
            join track t on t.album_id = va.album_id
            where t.id not in (select track_id id from exlude_track_ids)
            group by va.album_id
            order by max(va.release_date) desc
            limit :limit offset :skip
        """
        stmt = (
            text(stmt)
            .bindparams(
                min_date=min_date.strftime("%Y-%m-%d"),
                max_date=max_date.strftime("%Y-%m-%d"),
                limit=limit,
                skip=skip,
            )
            .columns(id=String)
        )
        return db.execute(stmt).fetchall()

    def get_by_date_range(
        self,
        db: Session,
        min_date: date,
        max_date: Optional[date] = date.today(),
        *,
        skip: int = 0,
        limit: int = 1_000,
    ) -> List[Album]:
        return (
            db.query(Album)
            .filter(Album.release_date >= min_date, Album.release_date <= max_date)
            .order_by(desc(Album.release_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_name(self, db: Session, name: str) -> Optional[List[Album]]:
        return db.query(Album).filter(Album.name == name).all()


album = CRUDAlbum(Album)

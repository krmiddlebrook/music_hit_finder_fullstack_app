from typing import List, Optional, Tuple, Union, Dict, Any, NamedTuple
from collections import defaultdict

from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import text, Integer, String, Float, Boolean, BigInteger
from celery.utils.log import get_task_logger


from app.crud.base import CRUDBase
from app.models.track import Track
from app.schemas.track import TrackCreate, TrackUpdate
from app.schemas.artist import ArtistCreate
from app.schemas.album import AlbumCreate
from app.schemas.track_artist import TrackArtistCreate
from app.schemas.track_rising import TrackRisingBase
from app import schemas
from app.spotify import parser

from .crud_track_artist import track_artist


logger = get_task_logger(__name__)


class CRUDTrack(CRUDBase[Track, TrackCreate, TrackUpdate]):
    def _format_track(
        self, obj_in: TrackCreate
    ) -> Tuple[schemas.Track, Dict[str, schemas.ArtistCreate]]:
        t_obj = schemas.Track(**obj_in.dict(exclude_unset=True))
        artists = {}
        if obj_in.artists:
            art_objs = parser.artist.from_artist_list(obj_in=obj_in.artists)
            artists = {a.id: a for a in art_objs}
        return (t_obj, artists)

    def create(self, db: Session, *, obj_in: TrackCreate,) -> Track:
        # push track artists -> push track album -> push track ->
        # push track <> artist associations
        t_obj, artists = self._format_track(obj_in=obj_in)
        db_track = super().create(db, obj_in=t_obj)
        # Push track <> artist id associations
        if artists:
            _ = track_artist.create_multi_from_track_ids(
                db, track_ids_artist_ids={t_obj.id: set(artists.keys())}
            )
        return db_track

    def create_multi(self, db: Session, *, objs_in: List[TrackCreate],) -> bool:
        """
        A convenience function to safely bulk insert a list or albums into the
        appropriate db table.
        """
        # Push tracks
        # Push track <> artist id associations
        tracks = []
        track_artist_pairs = defaultdict(set)
        for t in objs_in:
            t_obj, artists = self._format_track(obj_in=t)
            tracks.append(jsonable_encoder(t_obj))
            for aid in artists.keys():
                track_artist_pairs[t_obj.id].add(aid)

        push_successful = super().create_multi(db, objs_in=tracks)
        # Push track <> artist associations (we assume that the artists are already in
        # the artist table).
        if len(track_artist_pairs) > 0:
            _ = track_artist.create_multi_from_track_ids(
                db, track_ids_artist_ids=track_artist_pairs
            )
        return push_successful

    def get_tracks(self, db: Session, track_ids: List[str]) -> List[Track]:
        """
        Retrieve a list of db tracks.
        """
        return db.query(Track).filter(Track.id.in_(track_ids)).all()

    def get_rising_tracks(
        self,
        db: Session,
        *,
        lag_days: int = 7,
        release_date_lag: int = 365,
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
    ) -> List[TrackRisingBase]:
        # TODO: make track predictions optional and model_id dynamic
        # TODO: rn order by does nothing
        stmt = f"""
            select tr.track_id id,
                tr.playcount,
                tr.avg_chg chg,
                tr.avg_growth_rate growth_rate,
                tr.period_days,
                tr.prediction,
                tr.probability,
                tr.musicai_score
            from (
                select tp.*,
                    7 period_days,
                    prediction,
                    probability,
                    CASE
                        WHEN probability < 0.3 THEN 1
                        WHEN probability < 0.6 THEN 2
                        WHEN probability < 0.9 THEN 3
                        WHEN probability < 0.97 THEN 4
                        WHEN probability <= 1.0 THEN 5
                    END musicai_score
                from track_rising_rolling_{lag_days} tp
                join track_prediction tpred on tpred.track_id = tp.track_id
                where tpred.model_id = 'CNNSpectrogramV2_2019-11-25_100'
            ) tr
            where playcount between :min_playcount and :max_playcount
                and avg_chg between :min_chg and :max_chg
                and avg_growth_rate between :min_growth_rate and :max_growth_rate
                and probability between :min_probability and :max_probability
                and musicai_score between :min_musicai_score and :max_musicai_score
            order by (avg_growth_rate * probability) desc, playcount desc
            limit :limit offset :skip;
        """
        stmt = (
            text(stmt)
            .bindparams(
                min_playcount=min_playcount,
                max_playcount=max_playcount,
                min_chg=min_chg,
                max_chg=max_chg,
                min_growth_rate=min_growth_rate,
                max_growth_rate=max_growth_rate,
                min_probability=min_probability,
                max_probability=max_probability,
                min_musicai_score=min_musicai_score,
                max_musicai_score=max_musicai_score,
                limit=limit,
                skip=skip,
            )
            .columns(
                id=String,
                playcount=BigInteger,
                chg=Integer,
                growth_rate=Float,
                period_days=Integer,
                prediction=Float,
                probability=Float,
                musicai_score=Integer,
            )
        )

        tracks_rising = [
            TrackRisingBase(
                id=row[0],
                playcount=row[1],
                chg=row[2],
                growth_rate=row[3],
                period_days=row[4],
                prediction=row[5],
                probability=row[6],
                musicai_score=row[7],
            )
            for row in db.execute(stmt).fetchall()
        ]
        return tracks_rising

    def get_rising_tracks_missing_spectrograms(
        self,
        db: Session,
        *,
        lag_days: int = 7,
        order_by: str = "growth_rate",
        skip: int = 0,
        limit: int = 10_000,
    ) -> List[Tuple[str, str]]:
        # TODO: add lag days functionality
        if order_by in ("growth_rate", "chg"):
            order_by = f"avg_{order_by}"
        stmt = f"""
            select
                tr.track_id id,
                tr.preview_url
            from track_rising_rolling_{lag_days} tr
            left join spectrogram s on s.track_id = tr.track_id
            where (s.spectrogram is null or s.is_corrupt = true)
                and tr.preview_url is not null
            order by {order_by} desc
            limit :limit offset :skip;
        """
        stmt = (
            text(stmt)
            .bindparams(limit=limit, skip=skip,)
            .columns(id=String, preview_url=String,)
        )
        return db.execute(stmt).fetchall()

    def get_tracks_missing_spectrograms(
        self, db: Session, *, lag_days: int = 7, skip: int = 0, limit: int = 10_000,
    ) -> List[Track]:
        """
        Retrieve tracks missing spectrograms that have a preview url and are associated
        with whitelisted genres and verified artists. Tracks are returned in descending
        order based on their release date.
        """
        stmt = f"""
            with canidate_artists as (
                select a.id artist_id
                from artist a
                left join genre_artist ga on ga.artist_id = a.id
                where a.verified = true
                    and (
                        ga.genre_id not in (
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
                        or ga.genre_id is null
                    )
                group by a.id
            ), canidate_albums as (
                select al.id album_id,
                    max(al.name) album_name,
                    max(al.release_date) release_date
                from album al
                join album_artist aa on aa.album_id = al.id
                join canidate_artists ca on ca.artist_id = aa.artist_id
                where al.release_date between CURRENT_DATE - interval '{lag_days} days' and CURRENT_DATE
                group by al.id
            ), canidate_tracks as (
                select t.*
                from track t
                left join track_prediction tpred on tpred.track_id = t.id
                where tpred.track_id is null
                    and t.preview_url is not null
            ) select ct.id id,
                ct.name "name",
                ct.track_number track_number,
                ct.explicit explicit,
                ct.duration_ms duration_ms,
                ct.isrc isrc,
                ct.preview_url preview_url,
                ct.album_id album_id
            from canidate_tracks ct
            join canidate_albums cal on cal.album_id = ct.album_id
            left join spectrogram s on s.track_id = ct.id
            where s.track_id is null
            order by cal.release_date desc
            limit :limit offset :skip;
        """
        stmt = (
            text(stmt)
            .bindparams(limit=limit, skip=skip,)
            .columns(
                id=String,
                name=String,
                track_number=Integer,
                explicit=Boolean,
                duration_ms=Integer,
                isrc=String,
                preview_url=String,
                album_id=String,
            )
        )
        return db.execute(stmt).fetchall()

    def get_rising_tracks_to_predict(
        self,
        db: Session,
        *,
        lag_days: int = 30,
        order_by: str = "growth_rate",
        skip: int = 0,
        limit: int = 10_000,
    ) -> List[Tuple[str]]:
        # TODO: add lag days functionality
        if order_by in ("growth_rate", "chg"):
            order_by = f"avg_{order_by}"

        stmt = f"""
            select tr.track_id id
            from track_rising_rolling_{lag_days} tr
            join spectrogram s on s.track_id = tr.track_id
            left join track_prediction tpred on tpred.track_id = tr.track_id
            where s.is_corrupt is false
                and tpred.track_id is null
            order by {order_by} desc
            limit :limit offset :skip;
        """
        stmt = text(stmt).bindparams(limit=limit, skip=skip,).columns(id=String)
        return db.execute(stmt).fetchall()

    def get_tracks_missing_predictions(
        self, db: Session, *, lag_days: int = 7, skip: int = 0, limit: int = 10_000,
    ) -> List[Track]:
        """
        Retrieve tracks missing hit predictions that have a preview url and are
        associated with whitelisted genres and verified artists. Tracks are returned
        in descending order based on their release date.
        """
        stmt = f"""
            with canidate_artists as (
                select a.id artist_id
                from artist a
                left join genre_artist ga on ga.artist_id = a.id
                where a.verified = true
                    and (
                        ga.genre_id not in (
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
                        or ga.genre_id is null
                    )
                group by a.id
            ), canidate_albums as (
                select al.id album_id,
                    max(al.name) album_name,
                    max(al.release_date) release_date
                from album al
                join album_artist aa on aa.album_id = al.id
                join canidate_artists ca on ca.artist_id = aa.artist_id
                where al.release_date BETWEEN CURRENT_DATE - interval '{lag_days} days' AND CURRENT_DATE
                group by al.id
            ), canidate_tracks as (
                select t.*
                from track t
                join spectrogram s on s.track_id = t.id
                left join track_prediction tpred on tpred.track_id = t.id
                where tpred.track_id is null
                    and t.preview_url is not null
                    and s.is_corrupt = false
            ) select ct.id id,
                ct.name "name",
                ct.track_number track_number,
                ct.explicit explicit,
                ct.duration_ms duration_ms,
                ct.isrc isrc,
                ct.preview_url preview_url,
                ct.album_id album_id
            from canidate_tracks ct
            join canidate_albums cal on cal.album_id = ct.album_id
            order by cal.release_date desc
            limit :limit offset :skip;
        """
        stmt = (
            text(stmt)
            .bindparams(limit=limit, skip=skip,)
            .columns(
                id=String,
                name=String,
                track_number=Integer,
                explicit=Boolean,
                duration_ms=Integer,
                isrc=String,
                preview_url=String,
                album_id=String,
            )
        )
        return db.execute(stmt).fetchall()

    def get_tracks_missing_preview_url(
        self, db: Session, *, skip: int = 0, limit: int = 10_000
    ) -> List[Track]:
        stmt = """
            with valid_tracks as (
                select t.id id,
                    max(al.release_date) release_date
                from track t
                join album al on t.album_id = al.id
                left join album_artist aa on aa.album_id = al.id
                left join track_artist ta on ta.track_id = t.id
                left join genre_artist ga
                    on ga.artist_id = ta.artist_id
                    or ga.artist_id = aa.artist_id
                where t.preview_url is null
                    and al.release_date <= CURRENT_DATE
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
                group by t.id
                order by max(al.release_date) desc
                limit :limit offset :skip
            ) select id
            from valid_tracks vt
        """
        stmt = text(stmt).bindparams(limit=limit, skip=skip,).columns(id=String)
        return db.execute(stmt).fetchall()


track = CRUDTrack(Track)

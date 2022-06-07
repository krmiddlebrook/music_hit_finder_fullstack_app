from typing import Any, Dict, Optional, Union, List

from sqlalchemy import text, String, Float, Integer
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.core.security import get_password_hash, verify_password
from app.db.session import session_scope
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from .crud_spotify_user import spotify_user
from app.schemas.spotify_user import SpotifyUser


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_users_with_spotify_id(
        self, db: Session, *, limit: int = 1_000, skip: int = 0
    ) -> List[User]:
        return db.query(User).filter(User.spotify_id != None).all()  # noqa: E711

    def get_canidate_track_pairs_by_users(
        self,
        db: Session,
        *,
        spotify_ids: Optional[Union[List[str], str]] = None,
        user_limit: int = 1e7,
        user_skip: int = 0,
        lag_period: int = 7,
        days_since_release: int = 180,
        canidate_hit_limit: int = 1_500,
        limit: int = 50_000,
        skip: int = 0,
    ) -> List[Dict[str, str]]:
        """
        Retrieve canidate user track <> hit track pairs that aren't in the
        track_distance table.
        """
        if spotify_ids:
            if isinstance(spotify_ids, str):
                spotify_ids = spotify_ids.split(",")
            stmt = f"""
                with user_tracks as (
                    select tu.track_id
                    from track_user tu
                    join spectrogram s on s.track_id = tu.track_id
                    where tu.user_id in :spotify_ids
                ), canidate_hits as (
                    select
                        score_tr.*
                    from (
                        select tr.*,
                            {lag_period} period_days,
                            prediction,
                            probability,
                            CASE
                                WHEN probability < 0.3 THEN 1
                                WHEN probability < 0.6 THEN 2
                                WHEN probability < 0.9 THEN 3
                                WHEN probability < 0.97 THEN 4
                                WHEN probability <= 1.0 THEN 5
                            END musicai_score
                        from track_rising_rolling_{lag_period} tr
                        join track_prediction tpred on tpred.track_id = tr.track_id
                        where tpred.model_id = 'CNNSpectrogramV2_2019-11-25_100'
                    ) score_tr
                    left join user_tracks ut on ut.track_id = score_tr.track_id
                    where probability >= 0.70
                        and ut.track_id is null
                    order by probability desc
                    limit :canidate_hit_limit offset 0
                ), canidates as (
                    select
                        ut.track_id src_id,
                        ch.track_id tgt_id,
                        ch.probability
                    from canidate_hits ch
                    join user_tracks ut
                        on ut.track_id < ch.track_id
                        and ut.track_id is not null
                ) select
                    c.src_id,
                    c.tgt_id
                from canidates c
                left join track_distance td1
                    on td1.src_id = c.src_id
                    and td1.tgt_id = c.tgt_id
                left join track_distance td2
                    on td2.src_id = c.tgt_id
                    and td2.tgt_id = c.src_id
                where td1.src_id is null
                    and td2.src_id is null
                order by c.src_id, c.tgt_id
                limit :limit offset :skip;
            """
            stmt = (
                text(stmt)
                .bindparams(
                    canidate_hit_limit=canidate_hit_limit,
                    spotify_ids=tuple(spotify_ids),
                    limit=limit,
                    skip=skip,
                )
                .columns(src_id=String, tgt_id=String,)
            )
        else:
            stmt = """
                with user_tracks as (
                    select tu.track_id
                    from track_user tu
                    join spectrogram s on s.track_id = tu.track_id
                    where tu.user_id in (
                            select spotify_id
                            from "user"
                            where spotify_id is not null
                            limit :user_limit offset :user_skip
                        )
                ), canidate_hits as (
                    select
                        score_tr.*
                    from (
                        select tr.*,
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
                        from track_rising_rolling_7 tr
                        join track_prediction tpred on tpred.track_id = tr.track_id
                        where tpred.model_id = 'CNNSpectrogramV2_2019-11-25_100'
                    ) score_tr
                    left join user_tracks ut on ut.track_id = score_tr.track_id
                    where probability >= 0.70
                        and ut.track_id is null
                    order by probability desc
                    limit :canidate_hit_limit offset 0
                ), canidates as (
                    select
                        ut.track_id src_id,
                        ch.track_id tgt_id,
                        ch.probability
                    from canidate_hits ch
                    join user_tracks ut
                        on ut.track_id < ch.track_id
                        and ut.track_id is not null
                ) select
                    c.src_id,
                    c.tgt_id
                from canidates c
                left join track_distance td1
                    on td1.src_id = c.src_id
                    and td1.tgt_id = c.tgt_id
                left join track_distance td2
                    on td2.src_id = c.tgt_id
                    and td2.tgt_id = c.src_id
                where td1.src_id is null
                    and td2.src_id is null
                order by c.src_id, c.tgt_id
                limit :limit offset :skip;
            """
            stmt = (
                text(stmt)
                .bindparams(
                    user_limit=user_limit,
                    user_skip=user_skip,
                    canidate_hit_limit=canidate_hit_limit,
                    limit=limit,
                    skip=skip,
                )
                .columns(src_id=String, tgt_id=String,)
            )
        return [jsonable_encoder(row) for row in db.execute(stmt).fetchall()]

    def get_track_recs_for_user(
        self,
        db: Session,
        *,
        spotify_id: str,
        lag_period: int = 7,
        days_since_release: int = 180,
        limit: int = 40,
        skip: int = 0,
    ) -> List[Dict[str, str]]:
        """
        Retrieve track  <> hit track pairs that aren't in the
        track_distance table.
        """
        # TODO: refactor to use rising tracks materialized view
        stmt = f"""
            with pcnt as (
                select pc.track_id,
                    t.isrc,
                    t.name,
                    t.album_id,
                    al.release_date,
                    t.preview_url,
                    pc.date,
                    last_value(pc.playcount) OVER (PARTITION BY pc.track_id ORDER BY pc.date) playcount,
                    first_value(pc.playcount) OVER (PARTITION BY pc.track_id ORDER BY pc.date) start_playcount,
                    last_value(pc.playcount) OVER (PARTITION BY pc.track_id ORDER BY pc.date) - first_value(pc.playcount) OVER (PARTITION BY pc.track_id ORDER BY pc.date) chg
                from track_playcount pc
                join track t on t.id = pc.track_id
                join album al on al.id = t.album_id
                where playcount > 0
                    and pc.date >= CURRENT_DATE - interval '{str(lag_period)} days'
                    and t.preview_url is not null
                    and al.release_date BETWEEN CURRENT_DATE - interval '{str(days_since_release)} days' AND CURRENT_DATE
            ), filtered_pcnt as (
                select pc.track_id id,
                    pc.isrc,
                    pc.name track_name,
                    pc.album_id,
                    pc.release_date,
                    pc.preview_url,
                    pc.date,
                    a.id artist_id,
                    a.name artist_name,
                    pc.playcount,
                    pc.start_playcount,
                    pc.chg,
                    ((cast(playcount as DOUBLE PRECISION) / cast(start_playcount as DOUBLE PRECISION)) - 1) growth_rate,
                    row_number() over (partition by pc.track_id order by pc.date desc) as row_num
                from pcnt pc
                join track_artist ta on ta.track_id = pc.track_id
                join artist a on a.id = ta.artist_id
                join genre_artist ga on ga.artist_id = a.id
                where start_playcount is not null
                    and a.verified = true
                    and chg > 0
                    and pc.playcount BETWEEN 10000 AND 50000000
                    and 1 - (cast(chg as DOUBLE PRECISION) / cast(playcount as DOUBLE PRECISION)) >= 0.03
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
            ), final_tbl as (
                select fp.id,
                    fp.isrc,
                    playcount,
                    chg,
                    growth_rate,
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
                from filtered_pcnt fp
                join track_prediction tpred on tpred.track_id = fp.id
                where row_num = 1
                    and tpred.model_id = 'CNNSpectrogramV2_2019-11-25_100'
            ), reduce_identicals as (
                select id,
                    isrc,
                    playcount,
                    chg,
                    growth_rate,
                    period_days,
                    prediction,
                    probability,
                    musicai_score,
                    (CAST(musicai_score as DOUBLE PRECISION) * growth_rate) rank_col,
                    row_number() over (partition by isrc order by musicai_score desc) as row_num
                from final_tbl
                where musicai_score between 4 and 5
            ), user_tracks as (
                select tu.track_id id
                from track_user tu
                where tu.user_id = '{spotify_id}'
            ), canidate_hits as (
                select ri.id,
                    playcount,
                    chg,
                    growth_rate,
                    period_days,
                    prediction,
                    probability,
                    musicai_score,
                    rank_col
                from reduce_identicals ri
                left join user_tracks ut on ut.id = ri.id
                where row_num = 1
                    and ut.id is null
            ) select
                ch.id id,
                CAST(avg(td.distance) as INTEGER) avg_distance,
                CAST(PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY distance) as INTEGER) median
            from canidate_hits ch
            join track_distance td on (
                    (
                        td.src_id = ch.id
                        and td.tgt_id in (select id from user_tracks)
                    ) or
                    (
                        td.tgt_id = ch.id
                        and td.src_id in (select id from user_tracks)
                    )
                )
            group by ch.id
            order by median, avg_distance
            limit :limit offset :skip;
        """
        stmt = (
            text(stmt)
            .bindparams(limit=limit, skip=skip,)
            .columns(id=String, avg_distance=Integer, median=Integer)
        )
        return [jsonable_encoder(row) for row in db.execute(stmt).fetchall()]

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_superuser=obj_in.is_superuser,
        )
        if obj_in.spotify_id is not None:
            _ = spotify_user.create(db, obj_in=SpotifyUser(id=obj_in.spotify_id))
            db_obj.spotify_id = obj_in.spotify_id
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data.get("password", None):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        if update_data.get("spotify_id", None):
            with session_scope() as conn_db:
                spotify_user.create(
                    conn_db, obj_in=SpotifyUser(id=update_data["spotify_id"])
                )
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser


user = CRUDUser(User)

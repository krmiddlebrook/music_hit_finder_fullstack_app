from typing import Optional, List
from collections import defaultdict

from sqlalchemy.orm import Session
from celery.utils.log import get_task_logger

from app.crud.base import CRUDBase
from app.models.album_artist import Album_Artist
from app.schemas.album_artist import AlbumArtistCreate, AlbumArtistUpdate

logger = get_task_logger(__name__)


class CRUDAlbumArtist(CRUDBase[Album_Artist, AlbumArtistCreate, AlbumArtistUpdate]):
    def create(self, db: Session, *, album_id: str, artist_id: str) -> Album_Artist:
        obj_in = AlbumArtistCreate(album_id=album_id, artist_id=artist_id)
        return super().create(db, obj_in=obj_in, refresh=False)

    def create_multi_from_album_ids(
        self, db: Session, *, album_ids: List[str], artist_ids: List[List[str]]
    ) -> bool:
        """
        Create album_id <> artist_id pairs for each album in the album_ids list.
        `artist_ids` is a list of lists, where each sublist contains a set of
        artist ids to be paired with the album_id from the same index in the
        album_ids list.
        """
        db_pairs = defaultdict(set)
        for db_aa in (
            db.query(Album_Artist).filter(Album_Artist.album_id.in_(album_ids)).all()
        ):
            db_pairs[db_aa.album_id].add(db_aa.artist_id)

        canidate_pairs = []
        for alid, aids in zip(album_ids, artist_ids):
            for aid in aids:
                if aid not in db_pairs[alid]:
                    canidate_pairs.append(
                        AlbumArtistCreate(album_id=alid, artist_id=aid).dict()
                    )
        return super().create_multi(db, objs_in=canidate_pairs)

    def get(
        self, db: Session, *, album_id: str, artist_id: str
    ) -> Optional[Album_Artist]:
        return (
            db.query(Album_Artist)
            .filter(
                Album_Artist.album_id == album_id, Album_Artist.artist_id == artist_id
            )
            .first()
        )

    def get_artist_ids_by_album_id(self, db: Session, *, album_id: str) -> List[str]:
        artist_ids = [
            aa.artist_id
            for aa in db.query(Album_Artist)
            .filter(Album_Artist.album_id == album_id)
            .all()
        ]
        return artist_ids


album_artist = CRUDAlbumArtist(Album_Artist)

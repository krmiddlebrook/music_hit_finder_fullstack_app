from typing import Optional, List
from collections import defaultdict

# from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.artist_link import Artist_Link
from app.schemas.artist_link import ArtistLinkCreate, ArtistLinkUpdate


class CRUDArtistLink(CRUDBase[Artist_Link, ArtistLinkCreate, ArtistLinkUpdate]):
    def get(self, db: Session, *, link: str, artist_id: str) -> Optional[Artist_Link]:
        return (
            db.query(Artist_Link)
            .filter(Artist_Link.link == link, Artist_Link.artist_id == artist_id)
            .first()
        )

    # def create(self, db: Session, *, obj_in: ArtistLinkCreate):
    def create_multi_from_artist_ids(
        self, db: Session, *, artist_ids: List[str], links: List[List[ArtistLinkCreate]]
    ) -> bool:
        """
        Create artist_id <> link_id pairs for each link_id in the link_ids list.
        `link_ids` is a list of lists, where each sublist contains a set of
        link ids to be paired with the artist_id from the same index in the
        artist_ids list.
        """
        db_pairs = defaultdict(set)
        for db_al in (
            db.query(Artist_Link).filter(Artist_Link.artist_id.in_(artist_ids)).all()
        ):
            db_pairs[db_al.artist_id].add(db_al.link)

        canidate_pairs = []
        for aid, alinks in zip(artist_ids, links):
            for link in alinks:
                if link.link not in db_pairs[aid]:
                    canidate_pairs.append(link.dict())
        return super().create_multi(db, objs_in=canidate_pairs)


artist_link = CRUDArtistLink(Artist_Link)

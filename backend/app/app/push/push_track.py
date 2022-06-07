from typing import List

from sqlalchemy.orm import Session

from app import crud, schemas, models


class PushTrack(object):
    def push_track(
        self,
        db: Session,
        track: schemas.Track,
        artists: List[schemas.ArtistCreate] = [],
        album: schemas.AlbumCreate = None,
        album_artists: List[schemas.ArtistCreate] = [],
    ) -> models.Track:
        """
        Push track to db.
        """
        db_track = crud.track.get(db, id=track.id)
        if not db_track:
            db_track = crud.track.create(
                db,
                obj_in=track,
                artists=artists,
                album=album,
                album_artists=album_artists,
            )

        return db_track

    def push_track_playcount(
        self, db: Session, track_playcount: schemas.TrackPlaycount
    ) -> models.Track_Playcount:
        """
        Push track playcount to db.
        """
        db_track_pcnt = crud.track_playcount.get(db, id=track_playcount.id)
        if not db_track_pcnt:
            db_track_pcnt = crud.track_playcount.create(db, obj_in=track_playcount)

        return db_track_pcnt


track = PushTrack()

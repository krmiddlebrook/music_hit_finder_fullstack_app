from typing import Optional, List

from sqlalchemy.orm import Session

from app import crud, schemas, models
from app.spotify.spapi import spapi
from app.spotify import parser


class PushAlbum(object):
    def push_album(
        self,
        db: Session,
        album: schemas.Album,
        artists: List[schemas.ArtistCreate] = [],
        tracks: List[schemas.TrackCreate] = [],
        tracks_playcounts: List[schemas.TrackPlaycountCreate] = [],
    ) -> models.Album:
        """
        Push album to db.
        """
        db_album = crud.album.get(db, id=album.id)

        if not db_album:
            # get album tracks + playcounts
            if not tracks or not tracks_playcounts:
                al_resp = spapi.album_playcount(album.id)
                tracks = parser.track.from_album_playcount(obj_in=al_resp)
                tracks_playcounts = parser.track_playcount.from_album(obj_in=al_resp)

            db_album = crud.album.create(
                db,
                obj_in=album,
                artists=artists,
                tracks=tracks,
                tracks_playcounts=tracks_playcounts,
            )
        elif album.label and not db_album.label_id:
            if crud.label.get_by_name(db, name=album.label):
                db_label = crud.label.create(
                    db, obj_in=schemas.LabelCreate(name=album.label)
                )

            db_album.label_id = db_label.id
            db.commit()
            db.refresh(db_album)

        return db_album


album = PushAlbum()

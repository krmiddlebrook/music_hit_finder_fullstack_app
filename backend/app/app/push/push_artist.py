from sqlalchemy.orm import Session

from app import crud, schemas, models
from app.spotify.spapi import spapi
from app.spotify.spotify_mux import spotify_mux

from app.spotify import parser


class PushArtist(object):
    def push_artist(self, db: Session, artist: schemas.Artist) -> models.Artist:
        """
        Push artist to the db.
        """
        db_art = crud.artist.get(db, id=artist.id)
        if not db_art:
            # TODO: parallelize these requests
            a_info = spapi.artist_info(artist.id)
            if a_info:
                a_info = parser.artist.from_artist_info(obj_in=a_info)

                artist.verified = a_info.verified
                artist.active = a_info.active
                if not artist.name and a_info.name:
                    artist.name = a_info.name

            a_genres = spotify_mux.artist_about(artist.id)
            if a_genres:
                artist.genres = parser.genre.from_artist_about(obj_in=a_genres)

            db_art = crud.artist.create(db, obj_in=artist)
        elif db_art.verified is None and db_art.active is None:
            a_info = spapi.artist_info(artist.id)
            if a_info:
                a_info = parser.artist.from_artist_info(obj_in=a_info)
                db_art = crud.artist.update_status(
                    db, db_obj=db_art, new_info=a_info.dict()
                )
        elif not db_art.genres:
            a_genres = spotify_mux.artist_about(artist.id)
            if a_genres:
                a_genres = parser.genre.from_artist_about(obj_in=a_genres)
                db_art = crud.artist.update_genres(db, db_obj=db_art, genres=a_genres)

        return db_art


artist = PushArtist()

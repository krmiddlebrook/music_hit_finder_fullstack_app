from sqlalchemy.orm import Session

from app import crud, schemas, models


class PushGenre(object):
    def push_genre(self, db: Session, genre: schemas.Genre) -> models.Genre:
        """
        Push genre to db.
        """
        db_genre = crud.genre.get(db, id=genre.id)

        if not db_genre:
            db_genre = crud.genre.create(db, obj_in=genre)
            # logger.info(f"Genre created {genre}!")

        return db_genre


genre = PushGenre()

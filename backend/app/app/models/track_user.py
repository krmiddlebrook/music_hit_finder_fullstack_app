from sqlalchemy import Column, ForeignKey, String, Boolean

from app.db.base_class import Base


class Track_User(Base):
    track_id = Column(String, ForeignKey("track.id"), primary_key=True, index=True)
    user_id = Column(
        String, ForeignKey("spotify_user.id"), primary_key=True, index=True
    )
    top_track = Column(Boolean, default=False)
    source = Column(String, index=True)


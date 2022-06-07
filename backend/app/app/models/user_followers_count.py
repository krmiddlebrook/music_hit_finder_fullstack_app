from typing import TYPE_CHECKING
from datetime import date

from sqlalchemy import Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .spotify_user import Spotify_User  # noqa: F401


class User_Followers_Count(Base):
    # __tablename__ = "users_followers_counts"
    id = Column(String, primary_key=True, index=True)  # Format: <user_id>_<date>
    user_id = Column(String, ForeignKey("spotify_user.id"), index=True)
    date = Column(Date(), default=date.today, index=True)
    followers_count = Column(Integer, default=0)
    user = relationship("Spotify_User", back_populates="followers_counts")

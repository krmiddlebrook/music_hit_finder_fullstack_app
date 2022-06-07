# from datetime import date, datetime

# from sqlalchemy import Column, ForeignKey
# from app.db.base_class import Base
# from sqlalchemy.orm import relationship
# from sqlalchemy.types import (
#     BIGINT,
#     BOOLEAN,
#     INT,
#     SMALLINT,
#     Date,
#     DateTime,
#     Float,
#     Integer,
#     LargeBinary,
#     Text,
# )


# # >>> Association tables. <<< #


# class _TermPlaylist(Base):
#     __tablename__ = "terms_playlists"
#     term_id = Column(
#         Text(), ForeignKey("search_terms.term"), primary_key=True, index=True
#     )
#     playlist_id = Column(
#         Text(), ForeignKey("playlists.id"), primary_key=True, index=True
#     )


# class _TrackPlaylist(Base):
#     __tablename__ = "tracks_playlists"
#     track_id = Column(Text(), ForeignKey("tracks.id"), primary_key=True, index=True)
#     playlist_id = Column(
#         Text(), ForeignKey("playlists.id"), primary_key=True, index=True
#     )


# class _TrackUser(Base):
#     __tablename__ = "tracks_users"
#     track_id = Column(Text(), ForeignKey("tracks.id"), primary_key=True, index=True)
#     user_id = Column(
#         Text(), ForeignKey("spotify_users.id"), primary_key=True, index=True
#     )


# class _TrackArtist(Base):
#     __tablename__ = "tracks_artists"
#     track_id = Column(Text(), ForeignKey("tracks.id"), primary_key=True, index=True)
#     artist_id = Column(Text(), ForeignKey("artists.id"), primary_key=True, index=True)


# class _AlbumArtist(Base):
#     __tablename__ = "albums_artists"
#     album_id = Column(Text(), ForeignKey("albums.id"), primary_key=True, index=True)
#     artist_id = Column(Text(), ForeignKey("artists.id"), primary_key=True, index=True)


# class _GenreArtist(Base):
#     __tablename__ = "genres_artists"
#     genre_id = Column(Text(), ForeignKey("genres.id"), primary_key=True, index=True)
#     artist_id = Column(Text(), ForeignKey("artists.id"), primary_key=True, index=True)


# class _CityArtist(Base):
#     __tablename__ = "cities_artists"
#     city_id = Column(Text(), ForeignKey("cities.id"), primary_key=True, index=True)
#     artist_id = Column(Text(), ForeignKey("artists.id"), primary_key=True, index=True)


# class _TrackDistance(Base):
#     __tablename__ = "tracks_distances"
#     source_id = Column(Text(), ForeignKey("tracks.id"), primary_key=True, index=True)
#     target_id = Column(Text(), ForeignKey("tracks.id"), primary_key=True, index=True)
#     model_id = Column(Text(), ForeignKey("models.id"), primary_key=True, index=True)
#     distance_type = Column(Text(), primary_key=True, index=True)
#     distance = Column(Float())


# class _ModelResult(Base):
#     __tablename__ = "model_results"
#     track_id = Column(Text(), ForeignKey("tracks.id"), primary_key=True, index=True)
#     model_id = Column(Text(), ForeignKey("models.id"), primary_key=True, index=True)
#     prediction = Column(Float())
#     probability = Column(Float())
#     date = Column(DateTime(), default=datetime.now())


# # Normal Tables
# class _Model(Base):
#     __tablename__ = "models"
#     id = Column(Text(), primary_key=True, index=True)
#     path = Column(Text())
#     date = Column(DateTime(), default=datetime.now())


# class _Label(Base):
#     __tablename__ = "labels"
#     id = Column(INT(), primary_key=True, index=True)
#     name = Column(Text(), index=True)
#     albums = relationship("_Album", back_populates="label")


# class _User(Base):
#     __tablename__ = "spotify_users"
#     id = Column(Text(), primary_key=True, index=True)
#     name = Column(Text(), index=True)
#     followers_counts = relationship("_UserFollowersCount", back_populates="user")
#     playlists = relationship("_Playlist", back_populates="user")


# class _UserFollowersCount(Base):
#     __tablename__ = "users_followers_counts"
#     id = Column(Text(), primary_key=True, index=True)  # Format: <user_id>_<date>
#     user_id = Column(Text(), ForeignKey("spotify_users.id"), index=True)
#     date = Column(Date(), default=date.today, index=True)
#     followers_count = Column(INT(), default=0)
#     user = relationship("_User", back_populates="followers_counts")


# class _Playlist(Base):
#     __tablename__ = "playlists"
#     id = Column(Text(), primary_key=True, index=True)
#     owner_id = Column(Text(), ForeignKey("spotify_users.id"))
#     name = Column(Text(), index=True)
#     followers_counts = relationship(
#         "_PlaylistFollowersCount", back_populates="playlist"
#     )
#     search_terms = relationship(
#         "_SearchTerm", secondary="terms_playlists", back_populates="playlists"
#     )
#     user = relationship("_User", back_populates="playlists")
#     tracks = relationship(
#         "_Track", secondary="tracks_playlists", back_populates="playlists"
#     )


# class _PlaylistFollowersCount(Base):
#     __tablename__ = "playlists_followers_counts"
#     # TODO: change id to match format of user_followers_count, e.g., <playlist_id>_<date>
#     id = Column(INT(), primary_key=True, index=True)
#     playlist_id = Column(Text(), ForeignKey("playlists.id"))
#     followers_count = Column(INT())
#     date = Column(Date(), default=date.today, index=True)
#     playlist = relationship("_Playlist", back_populates="followers_counts")


# class _SearchTerm(Base):
#     __tablename__ = "search_terms"
#     term = Column(Text(), primary_key=True, index=True)
#     playlists = relationship(
#         "_Playlist", secondary="terms_playlists", back_populates="search_terms"
#     )


# class _Track(Base):
#     __tablename__ = "tracks"
#     id = Column(Text(), primary_key=True, index=True)
#     name = Column(Text(), index=True)
#     track_number = Column(INT())
#     explicit = Column(BOOLEAN())
#     duration_ms = Column(INT())
#     album_id = Column(Text(), ForeignKey("albums.id"), index=True)
#     album = relationship("_Album", back_populates="tracks")
#     playcounts = relationship("_TrackPlaycount", back_populates="track")
#     artists = relationship(
#         "_Artist", secondary="tracks_artists", back_populates="tracks"
#     )
#     playlists = relationship(
#         "_Playlist", secondary="tracks_playlists", back_populates="tracks"
#     )
#     spectrogram = relationship("_Spectrogram", uselist=False, back_populates="track")


# class _TrackPlaycount(Base):
#     __tablename__ = "tracks_playcounts"
#     id = Column(Text(), primary_key=True, index=True)  # Format: <track_id>_<date>
#     track_id = Column(Text(), ForeignKey("tracks.id"), index=True)
#     date = Column(Date(), default=date.today, index=True)
#     playcount = Column(INT())
#     popularity = Column(INT())
#     track = relationship("_Track", back_populates="playcounts")


# class _Album(Base):
#     __tablename__ = "albums"
#     id = Column(Text(), primary_key=True, index=True)
#     name = Column(Text(), index=True)
#     total_tracks = Column(INT())
#     release_date = Column(Date())
#     type = Column(Text())
#     label_id = Column(INT(), ForeignKey("labels.id"))
#     label = relationship("_Label", back_populates="albums")
#     tracks = relationship("_Track", back_populates="album")
#     artists = relationship(
#         "_Artist", secondary="albums_artists", back_populates="albums"
#     )


# class _Artist(Base):
#     __tablename__ = "artists"
#     id = Column(Text(), primary_key=True, index=True)
#     name = Column(Text(), index=True)
#     verified = Column(BOOLEAN(), default=False)
#     active = Column(BOOLEAN(), default=False)
#     stats = relationship("_ArtistStat", back_populates="artist")
#     links = relationship("_ArtistLink", back_populates="artist")
#     genres = relationship(
#         "_Genre", secondary="genres_artists", back_populates="artists"
#     )
#     top_cities = relationship("_CityCount", back_populates="artist")
#     cities = relationship("_City", secondary="cities_artists", back_populates="artists")
#     albums = relationship(
#         "_Album", secondary="albums_artists", back_populates="artists"
#     )
#     tracks = relationship(
#         "_Track", secondary="tracks_artists", back_populates="artists"
#     )


# class _ArtistStat(Base):
#     __tablename__ = "artists_stats"
#     id = Column(INT(), primary_key=True, index=True)
#     artist_id = Column(Text(), ForeignKey("artists.id"))
#     followers_count = Column(INT())
#     following_count = Column(INT())
#     monthly_listeners = Column(INT())
#     world_rank = Column(INT(), default=0)
#     date = Column(Date(), default=date.today, index=True)
#     artist = relationship("_Artist", back_populates="stats")


# class _ArtistLink(Base):
#     __tablename__ = "artists_links"
#     link = Column(Text(), primary_key=True, index=True)
#     artist_id = Column(Text(), ForeignKey("artists.id"), primary_key=True, index=True)
#     link_type = Column(Text(), index=True)
#     artist = relationship("_Artist", back_populates="links")


# class _Genre(Base):
#     __tablename__ = "genres"
#     id = Column(Text(), primary_key=True, index=True)
#     artists = relationship(
#         "_Artist", secondary="genres_artists", back_populates="genres"
#     )


# class _CityCount(Base):
#     __tablename__ = "cities_counts"
#     # TODO: change id to match format of tracks_playcounts, e.g., <city_id>_<artist_id>_<date>
#     id = Column(INT(), primary_key=True, index=True)
#     city_id = Column(Text(), ForeignKey("cities.id"), index=True)
#     artist_id = Column(Text(), ForeignKey("artists.id"), index=True)
#     listeners_count = Column(INT())
#     date = Column(Date(), default=date.today, index=True)
#     city = relationship("_City", back_populates="city_counts")
#     artist = relationship("_Artist", back_populates="top_cities")


# class _City(Base):
#     __tablename__ = "cities"
#     id = Column(Text(), primary_key=True, index=True)  # Format: city:region:country
#     city = Column(Text(), index=True)
#     region = Column(Text(), index=True)
#     country = Column(Text(), index=True)
#     city_counts = relationship("_CityCount", back_populates="city")
#     artists = relationship(
#         "_Artist", secondary="cities_artists", back_populates="cities"
#     )


# class _Spectrogram(Base):
#     __tablename__ = "spectrograms"
#     track_id = Column(Text(), ForeignKey("tracks.id"), primary_key=True, index=True)
#     spectrogram_type = Column(Text(), primary_key=True, index=True)
#     preview_url = Column(Text())
#     spectrogram = Column(LargeBinary())
#     track = relationship("_Track", back_populates="spectrogram", uselist=False)

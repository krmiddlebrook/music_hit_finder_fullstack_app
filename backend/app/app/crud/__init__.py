from .crud_item import item
from .crud_user import user
from .crud_track import track
from .crud_search_term import search_term
from .crud_spotify_user import spotify_user
from .crud_user_followers_count import user_followers_count
from .crud_playlist import playlist
from .crud_playlist_followers_count import playlist_followers_count
from .crud_term_playlist import term_playlist
from .crud_track import track
from .crud_artist import artist
from .crud_artist_link import artist_link
from .crud_album import album
from .crud_album_artist import album_artist
from .crud_track_artist import track_artist
from .crud_track_playlist import track_playlist
from .crud_track_playcount import track_playcount
from .crud_genre import genre
from .crud_genre_artist import genre_artist
from .crud_label import label
from .crud_spectrogram import spectrogram
from .crud_track_prediction import track_prediction
from .crud_ml_model import ml_model
from .crud_track_user import track_user
from .crud_track_distance import track_distance
from .crud_musicai_playlist import musicai_playlist
from .crud_materialized_view import materialized_view

# For a new basic set of CRUD operations you could just do

# from .base import CRUDBase
# from app.models.item import Item
# from app.schemas.item import ItemCreate, ItemUpdate

# item = CRUDBase[Item, ItemCreate, ItemUpdate](Item)

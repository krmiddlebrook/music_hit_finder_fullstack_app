# Import all the celery tasks here, so that Celery can register them.
from .search_term import flow_search_terms
from .track import push_track, push_tracks_playcounts, push_track_playcount
from .album import (
    flow_scrape_album_playcounts,
    read_album_playcount,
    push_album_playcount,
    push_album,
)
from .artist import read_artist_info, push_artists, push_artist
from .association import (
    push_term_x_playlist,
    push_album_x_artists,
    push_track_x_artists,
    push_track_x_playlist,
    push_artist_x_genres,
)

# from .track_playcount import push_tracks_playcounts, push_track_playcount
from .playlist import (
    flow_scrape_playlists,
    read_search_term_playlists,
    push_search_term_playlists,
    push_search_term_playlist,
    push_playlist_owner,
    push_playlist,
    push_playlist_followers_count,
)
from .playlist_track import (
    flow_scrape_playlists_tracks,
    read_playlist_tracks,
    push_playlist_tracks,
    push_playlist_track,
)
from .genre import push_genres_artist, push_genres, push_genre
from .spectrogram import flow_scrape_spectrograms, download_wav, push_spectrogram

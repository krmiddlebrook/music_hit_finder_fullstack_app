# Import all the celery tasks here, so that Celery can register them.
import app.spotify.track
import app.spotify.album
import app.spotify.artist
import app.spotify.playlist
import app.spotify.playlist_track
import app.spotify.genre
import app.spotify.track_playcount
import app.spotify.track_prediction
import app.spotify.track_distance
import app.spotify.spectrogram
import app.spotify.search_term
import app.spotify.association
import app.spotify.spotify_user
import app.spotify.flow
import app.spotify.spotify_mux
import app.spotify.spapi
import app.spotify.spotipy_mux

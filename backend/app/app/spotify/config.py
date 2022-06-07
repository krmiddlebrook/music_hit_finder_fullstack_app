# import shutil
# from pathlib import Path
from datetime import date

# Local file paths for audio (temporarly store mp3/wav) and misc files
# # (eg, search terms).
# SPOTIFY_DIR = Path("/app/app/spotify")
# TEMP_FILE_DIR = SPOTIFY_DIR / "files"
# SEARCH_TERMS_FILE = TEMP_FILE_DIR / "search_terms.txt"
# AUDIO_DIR = SPOTIFY_DIR / "audio"
# if AUDIO_DIR.exists():
#     shutil.rmtree(AUDIO_DIR)
# AUDIO_DIR.mkdir(parents=True, exist_ok=True)
# MP3_DIR = AUDIO_DIR / "mp3"
# MP3_DIR.mkdir(parents=True, exist_ok=True)
# WAV_DIR = AUDIO_DIR / "wav"
# WAV_DIR.mkdir(parents=True, exist_ok=True)


# Spotify Credentials
# dict with <key>:<value> as <username>:<{password, sp_dc, sp_key}>
# sp_dc and sp_key are associated with the username's sign-in cookies.
SPOTIFY_CREDS = {
    # TODO: insert spotify user account credentials here. (you can add more than one account too)
    # Example:
    "my_username": {
        "password": "my_password",
        "sp_dc": "UemmwNssj3A5S7CtMUk8sQ0OL2irR2qVhMwNdLnsGZ0plLmqzx4VnDowI",
        "sp_key": "09c3-114f-62at-ae65-e059baf2f",
    },
}

# Spotify developer credentials for Spotify API (used with Spotipy)
SPOTIPY_CREDS = [
    # TODO: insert spotify developer account credentials here.
    {
        "ID": "my_spotify_dev_id",
        "SECRET": "my_spotify_dev_secret_key",
    },
]
SPOTIPY_REQUESTS_TIMEOUT = 10


# Configs for collecting tracks and albums for artists
# The # of releases allowed in a release group (album, single) or the # of tracks
# allowed for a release for an artist.
MAX_RELEASE_COUNT = {"albums": 30, "singles": 100, "tracks": 32}
OLDEST_RELEASE = date(2017, 1, 1)  # The oldest release to collect.

# Popular Playlists
INFLUENTIAL_PLAYLIST_THRESH = 1000


# Banned (blacklisted) genres.
BLACKLISTED_GENRES = set(
    [
        "meditation",
        "musica de fondo",
        "pianissimo",
        "world meditation",
        "sleep",
        "background piano",
        "spa",
        "background",
        "atmosphere",
        "musica para ninos",
    ]
)

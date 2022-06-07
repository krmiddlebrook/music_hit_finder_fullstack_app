import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from .config import SPOTIPY_CREDS, SPOTIPY_REQUESTS_TIMEOUT

SPOTIPY_CLIENTS = []
for creds in SPOTIPY_CREDS:
    cm = SpotifyClientCredentials(
        client_id=creds.get("ID", None),
        client_secret=creds.get("SECRET", None),  # noqa: E501
    )
    SPOTIPY_CLIENTS.append(
        spotipy.Spotify(
            client_credentials_manager=cm, requests_timeout=SPOTIPY_REQUESTS_TIMEOUT,
        )
    )


class SpotipyMux(object):
    def __init__(self, starting_point=0):
        self.iter_count = starting_point

    def client(self):
        if self.iter_count >= len(SPOTIPY_CLIENTS):
            self.iter_count -= len(SPOTIPY_CLIENTS) + 1
        self.iter_count += 1
        return SPOTIPY_CLIENTS[self.iter_count % len(SPOTIPY_CLIENTS)]

    def token(self):
        return self.client().client_credentials_manager.get_access_token()

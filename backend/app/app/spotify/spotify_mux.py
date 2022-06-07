import time
from datetime import date, datetime
from typing import Optional, Dict, Any, Union, List

from celery.utils.log import get_task_logger

from .config import SPOTIFY_CREDS, INFLUENTIAL_PLAYLIST_THRESH
from .utils import chunkify
from app.core.celery_app import celery_app

from app import crud, schemas

# from app.spotify import parser

import pandas as pd
import requests
from requests.exceptions import ConnectTimeout, ReadTimeout
import spotify_token as st

# from celery import group
from sqlalchemy.orm import Session

# from .playlists_tracks import collect_playlists_tracks

logger = get_task_logger(__name__)

# Use redis queue to access spotify users across workers.
redis = celery_app.backend
REFRESH_TOKEN_THRESH = 120

for user, data in SPOTIFY_CREDS.items():
    expires_at = int(redis.get(f"SpotifyMux::{user}::expires_at") or b"0")
    if datetime.now() > datetime.fromtimestamp(expires_at):
        auth_token, expires_at = st.start_session(data["sp_dc"], data["sp_key"])
        redis.set(f"SpotifyMux::{user}::auth_token", auth_token)
        redis.set(f"SpotifyMux::{user}::expires_at", expires_at)


class SpotifyMux(object):
    def __init__(self, starting_point: int = 0):
        self.iter_count = starting_point
        self.sp_creds_list = list(SPOTIFY_CREDS.items())
        self.sp_creds_len = len(self.sp_creds_list)

    def _get_request(
        self,
        url: str,
        headers: Dict[str, Any],
        params: Optional[Dict[str, Any]],
        return_as: Optional[str] = "json",
        *,
        conn_timeout: int = 3,
        read_timeout: int = 10,
        sleep_time: float = 0.4,
    ) -> Union[Dict, requests.request, None]:
        result = None
        try:
            resp = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=(conn_timeout, read_timeout),
            )

            if resp.status_code == 429:
                time.sleep(sleep_time)
                resp = requests.get(
                    url,
                    headers=headers,
                    params=params,  # noqa: E231
                    timeout=(conn_timeout, read_timeout),
                )
            resp.raise_for_status()
            if resp.status_code == 200:
                if return_as:
                    result = resp.json()
                else:
                    result = resp
        except ConnectTimeout as conn_err:  # noqa: F841
            logger.info(f"ConnectTimeout for url: {url}")
        except ReadTimeout as read_err:  # noqa: F841
            logger.info(f"ReadTimeout for url: {url}")
        except Exception as e:
            logger.warning(f"UNKNOWN ERROR for url: {url},\n error: {e}")
        finally:
            return result

    def creds(self, user: Optional[str] = None):
        if user:
            return user, SPOTIFY_CREDS[user]

        if self.iter_count >= self.sp_creds_len:
            self.iter_count -= self.sp_creds_len + 1
        self.iter_count += 1
        return self.sp_creds_list[self.iter_count % self.sp_creds_len]

    def token(self, user: Optional[str] = None, tries: int = 0):
        user, data = self.creds(user=user)
        expires_at = int(redis.get(f"SpotifyMux::{user}::expires_at") or b"0")
        if datetime.now() >= datetime.fromtimestamp(expires_at - REFRESH_TOKEN_THRESH):
            try:
                auth_token, expires_at = st.start_session(data["sp_dc"], data["sp_key"])
            except requests.exceptions.ConnectionError as conn_err:
                logger.warning(
                    "Connection Error retrieving auth token w/ spotify_token \n"
                    f"{conn_err}"
                )
                if tries < 2:
                    return self.token(user=user, tries=tries + 1)

            redis.set(f"SpotifyMux::{user}::auth_token", auth_token)
            redis.set(f"SpotifyMux::{user}::expires_at", expires_at)
            return auth_token

        if redis.get(f"SpotifyMux::{user}::auth_token"):
            return redis.get(f"SpotifyMux::{user}::auth_token").decode("utf-8")
        else:
            if tries < 2:
                return self.token(user=user, tries=tries + 1)

    def username_and_token(self):
        user, data = self.creds()
        expires_at = int(redis.get(f"SpotifyMux::{user}::expires_at") or b"0")
        if datetime.now() >= datetime.fromtimestamp(expires_at - REFRESH_TOKEN_THRESH):
            auth_token, expires_at = st.start_session(data["sp_dc"], data["sp_key"])
            redis.set(f"SpotifyMux::{user}::auth_token", auth_token)
            redis.set(f"SpotifyMux::{user}::expires_at", expires_at)

        auth_token = redis.get(f"SpotifyMux::{user}::auth_token").decode(
            "utf-8"
        )  # noqa: E501
        return (user, auth_token)

    def artist_discography(self, artist_id: str) -> Union[Dict, requests.request, None]:
        url = f"https://spclient.wg.spotify.com/artist/v1/{artist_id}"
        headers = {"Authorization": f"Bearer {self.token()}"}
        params = {
            "market": "from_token",
            "platform": "desktop",
            "catalogue": "premium",
            "format": "json",
        }
        return self._get_request(url, headers, params, return_as="json")

    def artist_about(self, artist_id: str) -> Union[Dict, requests.request, None]:
        """ Retrieves the artist metadata returned by the public spotify api.
        Ex:
            {
              "external_urls": {
                "spotify": "https://open.spotify.com/artist/6Z0Cmu4TIqYn3s5iJyLhP2"
              },
              "followers": {
                "href": null,
                "total": 5610
              },
              "genres": [
                "meditation",
                "musica de fondo",
                "pianissimo",
                "world meditation"
              ],
              "href": "https://api.spotify.com/v1/artists/6Z0Cmu4TIqYn3s5iJyLhP2",
              "id": "6Z0Cmu4TIqYn3s5iJyLhP2",
              "images": [
                {
                  "height": 640,
                  "url": "https://i.scdn.co/image/ab67616d0000b27387d957cce11893bf31ae4af0",
                  "width": 640
                },
                {
                  "height": 300,
                  "url": "https://i.scdn.co/image/ab67616d00001e0287d957cce11893bf31ae4af0",
                  "width": 300
                },
                {
                  "height": 64,
                  "url": "https://i.scdn.co/image/ab67616d0000485187d957cce11893bf31ae4af0",
                  "width": 64
                }
              ],
              "name": "Marcelo A. Rodríguez",
              "popularity": 43,
              "type": "artist",
              "uri": "spotify:artist:6Z0Cmu4TIqYn3s5iJyLhP2"
            }
        See https://developer.spotify.com/console/get-artist/?id=0OdUWJ0sBjDrqHygGUXe
        for more details.
        """
        url = f"https://api.spotify.com/v1/artists/{artist_id}"
        headers = {
            "Authorization": f"Bearer {self.token()}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        return self._get_request(url, headers, params=None, return_as="json")

    def artist_info(self, artist_id: str) -> Union[Dict, requests.request, None]:
        """ Retrieves artist info metadata. This function is basically deprecated,
            instead use the faster version in the SpApi class (see spapi.py).
        """
        url = f"https://spclient.wg.spotify.com/open-backend-2/v1/artists/{artist_id}"
        headers = {"Authorization": f"Bearer {self.token()}"}
        params = {
            "market": "from_token",
            "platform": "desktop",
            "catalogue": "premium",
            "format": "json",
        }
        return self._get_request(url, headers, params, return_as="json")

    def album_playcounts(self, album_id: str) -> Union[Dict, requests.request, None]:
        url = f"https://spclient.wg.spotify.com/album/v1/album-app/album/spotify:album:{album_id}/desktop"
        headers = {"Authorization": f"Bearer {self.token()}"}
        params = {"catalogue": "premium", "format": "json"}
        return self._get_request(url, headers, params, return_as="json")

    def tracks(
        self,
        track_ids: Union[List[str], str],
        conn_timeout: int = 3,
        read_timeout: int = 10,
        sleep_time: float = 0.4,
    ) -> Union[List[Dict], requests.request, None]:
        if isinstance(track_ids, list):
            track_ids = ",".join(track_ids)
        tracks = []
        try:
            resp = requests.get(
                f"https://api.spotify.com/v1/tracks/?ids={track_ids}",  # noqa: E501
                headers={"Authorization": f"Bearer {self.token()}"},
                params={"catalogue": "premium", "format": "json",},  # noqa: E231
                timeout=(conn_timeout, read_timeout),
            )
            if resp.status_code == 429:
                time.sleep(sleep_time)
                resp = requests.get(
                    f"https://api.spotify.com/v1/tracks/?ids={track_ids}",  # noqa: E501
                    headers={"Authorization": f"Bearer {self.token()}"},
                    params={"catalogue": "premium", "format": "json",},  # noqa: E231
                    timeout=(conn_timeout, read_timeout),
                )
            resp.raise_for_status()
            if resp.status_code == 200:
                tracks += resp.json()["tracks"]
        except ConnectTimeout as conn_err:  # noqa: F841
            logger.info(f"ConnectTimeout for tracks: {track_ids}")
        except ReadTimeout as read_err:  # noqa: F841
            logger.info(f"ReadTimeout for tracks: {track_ids}")
        except Exception as e:
            logger.warning(f"UNKNOWN request for tracks: {track_ids},\n error: {e}")
        return tracks

    def track(
        self,
        track_id: str,
        conn_timeout: int = 3,
        read_timeout: int = 10,
        sleep_time: float = 0.4,
    ) -> Union[Dict, None]:
        tracks = self.tracks([track_id], conn_timeout, read_timeout, sleep_time,)
        return tracks[0] if len(tracks) > 0 else None

    def user_tracks(
        self, db: Session, user_id: str, max_tracks: int = 500
    ) -> List[str]:
        # TODO: move all logic that doesn't directly involve getting the user's
        # tracks somewhere else.
        todays_date = date.today()
        todays_date_str = todays_date.strftime("%Y-%m-%d")

        # Check if user is in the users table, and add them and all their
        # follower/following users to the table if they do not exist there yet.
        users_dict = {}
        users_followers_counts = {}
        user = crud.spotify_user.get(db, id=user_id)
        if not user:
            users_dict[user_id] = dict(id=user_id)
            url = f"https://spclient.wg.spotify.com/user-profile-view/v3/profile/{user_id}/followers"

            headers = {"Authorization": f"Bearer {self.token(user=user_id)}"}
            params = {"market": "from_token"}
            result = self._get_request(url, headers, params, return_as="json")

            followers = result.get("profiles", []) if result else []
            followers_count = len(followers)
            # Add the users associated with the given user_id.
            # TODO: also retrieve the name associated with this user.
            u_fcnt_id = f"{user_id}_{todays_date_str}"  # user's follower counts id
            if u_fcnt_id not in users_followers_counts:
                users_followers_counts[u_fcnt_id] = dict(
                    id=u_fcnt_id,
                    user_id=user_id,
                    followers_count=followers_count,
                    date=todays_date,
                )

            # Add all the users associated with this user.
            for u in followers:
                if u.get("uri", None):
                    uid = u["uri"].split(":")[-1]
                    # Add the user to the users table.
                    if (
                        crud.spotify_user.get(db, id=uid) is None
                        and uid not in users_dict
                    ):
                        users_dict[uid] = dict(id=uid, name=u.get("name", None))
                    # Add the user's follower count to the
                    # users_followers_counts table.
                    u_fcnt_id = f"{uid}_{todays_date_str}"
                    if (
                        crud.user_followers_count.get(db, id=u_fcnt_id) is None
                        and u_fcnt_id not in users_followers_counts
                    ):
                        users_followers_counts[u_fcnt_id] = dict(
                            id=u_fcnt_id,
                            user_id=uid,
                            followers_count=followers_count,
                            date=todays_date,
                        )

            # Push users to the users table.
            crud.spotify_user.create_multi(db, obj_in=users_dict, logger=logger)
            # Push user-followersCount to the users_followers_counts table.
            crud.user_followers_count.create_multi(
                db, obj_in=users_followers_counts, logger=logger
            )

        # Get the user's most recent playlists (up to 200 most recent).
        playlists = []
        url = f"https://spclient.wg.spotify.com/user-profile-view/v3/profile/{user_id}/playlists"
        headers = {"Authorization": f"Bearer {self.token(user=user_id)}"}
        params = {"market": "from_token", "offset": "0", "limit": "200"}
        result = self._get_request(url, headers, params, return_as="json")
        if result:
            playlists.extend(result.get("public_playlists", []))

        # Add playlists to the playlists table if they don't exist in it yet.
        users_dict = {}
        playlists_dict = {}
        playlists_followers_counts_list = []
        for p in playlists:
            if p.get("uri", None):
                pid = p["uri"].split(":")[-1]
                owner_id = user_id
                if p.get("owner_uri", None):
                    owner_id = p["owner_uri"].split(":")[-1]
                # Check if the playlist exists in the playlists table.
                if crud.playlist.get(db, id=pid) is None and pid not in playlists_dict:
                    followers_count = p.get("followers_count", 0)

                    # Check if owner_id needs to be added to the users table.
                    if (
                        crud.spotify_user.get(db, id=owner_id) is None
                        and owner_id not in users_dict
                    ):
                        users_dict[owner_id] = dict(id=owner_id)

                    playlists_dict[pid] = dict(
                        id=pid, owner_id=owner_id, name=p.get("name", None)
                    )

                    # Add the playlist followers count data to the
                    # playlists_followers_counts table.
                    # TODO: update the id to match the format <playlist_id>_<date>
                    p_fcnt_id = f"{pid}_{todays_date_str}"
                    if crud.playlist_followers_count.get(db, id=p_fcnt_id) is None:
                        playlists_followers_counts_list.append(
                            dict(
                                id=p_fcnt_id,
                                playlist_id=pid,
                                followers_count=followers_count,
                                date=todays_date,
                            )
                        )

        # TODO: update push to new crud
        # Push users to the users table.
        crud.spotify_user.create_multi(db, obj_in=users_dict, logger=logger)
        # Push playlists to the playlists table.
        crud.playlist.create_multi(db, obj_in=playlists_dict, logger=logger)
        # Push playlists-followersCount to the playlists_followers_counts table.
        crud.playlist_followers_count.create_multi(
            db, obj_in=playlists_followers_counts_list, logger=logger
        )

        # Add the tracks associated with the playlists that were just added to
        # the playlists table.
        logger.info(f"Collected Playlist IDS = {list(playlists_dict.keys())}.")
        playlists_ids = chunkify(list(playlists_dict.keys()), chunk_size=10)
        # playlist_tracks_tasks = group(
        #     collect_playlists_tracks.s(pids, idx, max_tracks_playlist=200)
        #     for idx, pids in enumerate(playlists_ids)
        # )
        # tracks_tasks_flow = playlist_tracks_tasks.apply_async()
        # tracks_tasks_complete = tracks_tasks_flow.get()

        # Get tracks associated with this user_id
        # TODO: build crud, schema for track_user association
        query = f"""
            select track_id
            from tracks_users
            where user_id = '{user_id}'
            limit {max_tracks};
        """
        with db.connection() as conn:
            track_ids = pd.read_sql(query, con=conn).track_id.to_list()
        db.close()
        return track_ids

    def search_term_playlists(
        self, search_term: str, limit: int = 500
    ) -> List[Dict[str, Any]]:
        collected = 0
        playlists = []
        username, token = self.username_and_token()
        url = f"https://spclient.wg.spotify.com/searchview/km/v4/search-playlists/{search_term}"  # noqa: E501
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "country": "US",
            "username": f"{username}",
            "catalogue": "premium",
            "locale": "en",
            "platform": "desktop",
            "entityVersion": 2,
            "limit": 100,
        }
        while url and collected < limit:
            result = self._get_request(url, headers, params, return_as="json")
            if result is None:
                break
            elif result.get("results", None):
                plists = result["results"].get("playlists", {"hits": []}).get("hits")
                # Loop through returned playlists.
                for p in plists:
                    if p.get(
                        "followersCount", 0
                    ) > INFLUENTIAL_PLAYLIST_THRESH and p.get("uri", None):
                        collected += 1  # update collected iter
                        playlists.append(p)

                # Update the url or break the loop.
                next_url = result.get("loadMoreURI", None)
                if collected < limit and next_url != url:
                    url = next_url
                else:
                    url = None
            else:
                break

        return playlists

    def playlist(self, playlist_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve a spotify playlist object.

        More info:
            https://developer.spotify.com/documentation/web-api/reference/playlists/get-playlist/
        """
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
        if not token:
            token = self.token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "additional_types": "track",
            "market": "from_token",
        }
        return self._get_request(url, headers, params)

    def playlist_tracks(
        self, playlist_id: str, limit: int = 200, token: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        collected = 0
        tracks = []
        # username, token = self.token()
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"  # noqa: E501
        if not token:
            token = self.token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "offset": 0,
            "limit": 100,
            "additional_types": "track",
            "market": "from_token",
        }
        while url and collected < limit:
            result = self._get_request(url, headers, params, return_as="json")
            if result is None:
                break
            elif result.get("items", None):
                tracks += result["items"]
                collected += len(result["items"])

                # Update the url and params or break the loop.
                next_url = result.get("next", None)
                if collected < limit and next_url != url and next_url:
                    url = next_url
                    params["offset"] = result["offset"]
                    params["limit"] = result["limit"]
                else:
                    url = None
            else:
                break

        tracks = [
            t["track"]
            for t in tracks
            if t.get("track", {}) and t.get("track", {}).get("id", None)
        ]

        return tracks

    def refresh_tokens(self):
        # Deprecated.
        for user, password in SPOTIFY_CREDS.items():
            auth_token, expires_at = st.start_session(user, password)
            redis.set(f"SpotifyMux::{user}::auth_token", auth_token)
            redis.set(f"SpotifyMux::{user}::expires_at", expires_at)

    def print_tokens(self):
        for user, password in SPOTIFY_CREDS.items():
            auth_token = redis.get(f"SpotifyMux::{user}::auth_token")
            expires_at = redis.get(f"SpotifyMux::{user}::expires_at")
            print(user, auth_token, expires_at)


spotify_mux = SpotifyMux(0)

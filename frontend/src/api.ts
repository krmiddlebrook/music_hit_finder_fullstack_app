import axios from 'axios';
import querystring from 'querystring';
import spotifyAPI from 'spotify-web-api-js';
import {
  apiUrl,
  spotifyClientID,
  spotifyClientSecret,
  spotifyScopes,
  spotifyRedirectURI,
} from '@/env';
import {
  ISpotifyAuthCode,
  ISpotifyToken,
  IUserProfile,
  IUserProfileUpdate,
  IUserProfileCreate,
  IAlbum,
  IArtist,
  ITrack,
  IRisingTrackParams,
  IRisingTrack,
} from '@/interfaces';
import { readSpotifyToken } from '@/store/main/getters';

function authHeaders(token: string) {
  return {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  };
}

export const api = {
  async logInGetToken(username: string, password: string) {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    return axios.post(`${apiUrl}/api/v1/login/access-token`, params);
  },
  async spotifyGetAuthURL() {
    // see https://developer.spotify.com/documentation/general/guides/authorization-guide/#authorization-code-flow
    // for more details.
    const qstr = querystring.stringify({
      response_type: 'code',
      client_id: spotifyClientID,
      scope: spotifyScopes,
      redirect_uri: spotifyRedirectURI,
    });

    // return axios.get('https://accounts.spotify.com/authorize', {
    //   params: params,
    // });
    const authURL = 'https://accounts.spotify.com/authorize?' + qstr;
    return authURL;
  },
  // async spotifyGetAuthCode() {
  //   const url = `${apiUrl}/api/v1/spotify/callback`;
  //   // return axios.get()
  // },
  async spotifyGetToken(code: string) {
    // see https://developer.spotify.com/documentation/general/guides/authorization-guide/#authorization-code-flow
    // for more details.
    const headers = {
      headers: {
        Authorization:
          'Basic ' + btoa(`${spotifyClientID}:${spotifyClientSecret}`),
      },
    };
    const params = new URLSearchParams();
    params.append('grant_type', 'authorization_code');
    params.append('code', code);
    params.append('redirect_uri', spotifyRedirectURI);

    return axios.post<ISpotifyToken>(
      'https://accounts.spotify.com/api/token',
      params,
      headers
    );
  },
  async spotifyRefreshToken(refreshToken: string) {
    // see https://developer.spotify.com/documentation/general/guides/authorization-guide/#authorization-code-flow
    // for more details.
    const headers = {
      headers: {
        Authorization:
          'Basic ' + btoa(`${spotifyClientID}:${spotifyClientSecret}`),
      },
    };
    const params = new URLSearchParams();
    params.append('grant_type', 'refresh_token');
    params.append('client_id', spotifyClientID);
    params.append('refresh_token', refreshToken);

    return axios.post<ISpotifyToken>(
      'https://accounts.spotify.com/api/token',
      params,
      headers
    );
  },
  async spotifyMe(token: string) {
    return axios
      .get('https://api.spotify.com/v1/me', authHeaders(token))
      .then((response) => {
        if (response.status === 200 && response.data) {
          // console.log(response.data);
          const spotifyProfile = {
            id: response.data.id,
            name: response.data.display_name,
          };
          return spotifyProfile;
        }
      })
      .catch((err) => {
        console.log(err);
        if (err.response) {
          // console.log("Poop! Couldn't log into spotify!");
        }
      });
  },
  async saveSpotifyMe(token: string, spotify_token: string) {
    return axios
      .get('https://api.spotify.com/v1/me', authHeaders(spotify_token))
      .then((response) => {
        if (response.status === 200 && response.data) {
          console.log(response.data);
          const spotifyProfile = {
            id: response.data.id,
            name: response.data.display_name,
          };
          return spotifyProfile;
        }
      })
      .catch((err) => {
        console.log(err);

        if (err.response) {
          console.log("Poop! Couldn't log into spotify.");
        }
      });
  },
  async saveTrack(token: string, track_id: string) {
    const params = new URLSearchParams();
    params.append('ids', track_id);
    return axios.put(
      'https://api.spotify.com/v1/me/tracks',
      [track_id],
      authHeaders(token)
    );
  },
  async getUserTop(token: string, type: string, time_range: string) {
    // Retrieve this users top 50 Spotify artists or tracks (type) over three time ranges (long_term, medium_term, short_term)
    // https://developer.spotify.com/documentation/web-api/reference/personalization/get-users-top-artists-and-tracks/
    const queryParams = querystring.stringify({
      limit: 50,
      offset: 0,
      time_range: time_range,
    });
    const url = `https://api.spotify.com/v1/me/top/${type}?${queryParams}`;
    return axios.get(url, authHeaders(token));
  },
  async getMe(token: string) {
    return axios.get<IUserProfile>(
      `${apiUrl}/api/v1/users/me`,
      authHeaders(token)
    );
  },
  async updateMe(token: string, data: IUserProfileUpdate) {
    return axios.put<IUserProfile>(
      `${apiUrl}/api/v1/users/me`,
      data,
      authHeaders(token)
    );
  },
  async getUsers(token: string) {
    return axios.get<IUserProfile[]>(
      `${apiUrl}/api/v1/users/`,
      authHeaders(token)
    );
  },
  async updateUser(token: string, userId: number, data: IUserProfileUpdate) {
    return axios.put(
      `${apiUrl}/api/v1/users/${userId}`,
      data,
      authHeaders(token)
    );
  },
  async createUser(data: IUserProfileCreate) {
    return axios.post(`${apiUrl}/api/v1/users/create`, data);
  },
  async getUserPlaylist(token: string, spotify_token: string) {
    const { topArtists, topTracks } = await axios
      .all([
        this.getUserTop(spotify_token, 'artists', 'long_term'),
        this.getUserTop(spotify_token, 'tracks', 'long_term'),
        this.getUserTop(spotify_token, 'tracks', 'medium_term'),
        this.getUserTop(spotify_token, 'tracks', 'short_term'),
      ])
      .then(
        axios.spread(
          (topArtistsLong, topTracksLong, topTracksMedium, topTracksShort) => ({
            topArtists: topArtistsLong.data.items,
            topTracks: topTracksLong.data.items.concat(
              topTracksMedium.data.items,
              topTracksShort.data.items
            ),
          })
        )
      );
    const data = {
      top_artists: topArtists,
      top_tracks: topTracks,
      spotify_token: spotify_token,
    };
    return axios.post(
      `${apiUrl}/api/v1/users/me/playlist`,
      data,
      authHeaders(token)
    );
  },
  async createUserFromAdmin(token: string, data: IUserProfileCreate) {
    return axios.post(`${apiUrl}/api/v1/users/`, data, authHeaders(token));
  },
  async passwordRecovery(email: string) {
    return axios.post(`${apiUrl}/api/v1/password-recovery/${email}`);
  },
  async resetPassword(password: string, token: string) {
    return axios.post(`${apiUrl}/api/v1/reset-password/`, {
      new_password: password,
      token,
    });
  },
  async getRisingTracks(token: string, params: IRisingTrackParams) {
    return axios.get<IRisingTrack[]>(`${apiUrl}/api/v1/tracks/rising-tracks`, {
      params: params,
      ...authHeaders(token),
    });
  },
};

import {
  ISpotifyToken,
  IUserProfile,
  IRisingTrack,
  IUserPlaylist,
} from '@/interfaces';
import { MainState, AppNotification } from './state';
import { getStoreAccessors } from 'typesafe-vuex';
import { State } from '../state';
import {
  trackArtists,
  saveLocalSpotifyToken,
  saveLocalSpotifyRefreshToken,
  saveLocalSpotifyExpiresAt,
} from '../../utils';

export const mutations = {
  setLoggedInSpotify(state: MainState, payload: boolean) {
    state.isLoggedInSpotify = payload;
  },

  setSpotifyAuthCode(state: MainState, payload: string) {
    state.spotifyAuthCode = payload;
  },

  setSpotifyToken(state: MainState, payload: ISpotifyToken) {
    const newToken = payload;
    const inMillis = newToken.expires_in * 1000;
    newToken.expires_at = Date.now() + inMillis;

    // console.log('Old spotify token: ', state.spotifyToken);
    // console.log('New spotify token: ', newToken);
    if (!newToken.refresh_token) {
      newToken.refresh_token = state.spotifyToken.refresh_token;
    }
    state.spotifyToken = newToken;

    // saveLocalSpotifyToken(state.spotifyToken.access_token);
    // if (state.spotifyToken.refresh_token) {
    // saveLocalSpotifyRefreshToken(state.spotifyToken.refresh_token);
    // console.log('Local Spotify Refresh Token Saved!');
    // }
    // saveLocalSpotifyExpiresAt(state.spotifyToken.expires_at);
    // console.log('Local Spotify Token Saved: ', state.spotifyToken);
  },

  setToken(state: MainState, payload: string) {
    state.token = payload;
  },
  setLoggedIn(state: MainState, payload: boolean) {
    state.isLoggedIn = payload;
  },
  setLogInError(state: MainState, payload: boolean) {
    state.logInError = payload;
  },
  setUserProfile(state: MainState, payload: IUserProfile) {
    state.userProfile = payload;
  },
  setDashboardMiniDrawer(state: MainState, payload: boolean) {
    state.dashboardMiniDrawer = payload;
  },
  setDashboardShowDrawer(state: MainState, payload: boolean) {
    state.dashboardShowDrawer = payload;
  },
  addNotification(state: MainState, payload: AppNotification) {
    state.notifications.push(payload);
  },
  removeNotification(state: MainState, payload: AppNotification) {
    state.notifications = state.notifications.filter(
      (notification) => notification !== payload
    );
  },
  setRisingTracks(state: MainState, payload: IRisingTrack[]) {
    let fullTracks = payload.map((t) => {
      const newT = Object.assign(t, {
        progress: 0,
        artists_str: trackArtists(t),
        name: t.track.name,
        album_name: t.album.name,
        player: new Audio(t.track.preview_url),
        score_growth: t.musicai_score * t.growth_rate,
      });
      return newT;
    });

    if (state.risingTracks.length > 0) {
      fullTracks.forEach((t) => {
        if (state.risingTracks.some((e) => e.id === t.id) === false) {
          /* risingTracks doesn't contain the element */
          state.risingTracks.push(t);
        }
      });
      // state.risingTracks = [...fullTracks, ...state.risingTracks];
    } else {
      state.risingTracks = fullTracks;
    }
  },
  setCurrentTrack(state: MainState, payload: IRisingTrack) {
    state.currentTrack = payload;
  },
  setUserPlaylist(state: MainState, payload: IUserPlaylist) {
    state.userPlaylist = payload;
  },
};

const { commit } = getStoreAccessors<MainState | any, State>('');

export const commitSetDashboardMiniDrawer = commit(
  mutations.setDashboardMiniDrawer
);
export const commitSetDashboardShowDrawer = commit(
  mutations.setDashboardShowDrawer
);
export const commitSetLoggedInSpotify = commit(mutations.setLoggedInSpotify);
export const commitSetSpotifyAuthCode = commit(mutations.setSpotifyAuthCode);
export const commitSetSpotifyToken = commit(mutations.setSpotifyToken);
export const commitSetLoggedIn = commit(mutations.setLoggedIn);
export const commitSetLogInError = commit(mutations.setLogInError);
export const commitSetToken = commit(mutations.setToken);
export const commitSetUserProfile = commit(mutations.setUserProfile);
export const commitAddNotification = commit(mutations.addNotification);
export const commitRemoveNotification = commit(mutations.removeNotification);
export const commitSetRisingTracks = commit(mutations.setRisingTracks);
export const commitSetCurrentTrack = commit(mutations.setCurrentTrack);
export const commitSetUserPlaylist = commit(mutations.setUserPlaylist);

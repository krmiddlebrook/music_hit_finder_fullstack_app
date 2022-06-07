import { MainState } from './state';
import { getStoreAccessors } from 'typesafe-vuex';
import { State } from '../state';

export const getters = {
  hasAdminAccess: (state: MainState) => {
    return (
      state.userProfile &&
      state.userProfile.is_superuser &&
      state.userProfile.is_active
    );
  },
  loginError: (state: MainState) => state.logInError,
  dashboardShowDrawer: (state: MainState) => state.dashboardShowDrawer,
  dashboardMiniDrawer: (state: MainState) => state.dashboardMiniDrawer,
  userProfile: (state: MainState) => state.userProfile,
  token: (state: MainState) => state.token,
  isLoggedIn: (state: MainState) => state.isLoggedIn,
  firstNotification: (state: MainState) =>
    state.notifications.length > 0 && state.notifications[0],
  spotifyAuthCode: (state: MainState) => state.spotifyAuthCode,
  isLoggedInSpotify: (state: MainState) => state.isLoggedInSpotify,
  spotifyToken: (state: MainState) => state.spotifyToken,
  risingTracks: (state: MainState) => state.risingTracks,
  currentTrack: (state: MainState) => state.currentTrack,
  userPlaylist: (state: MainState) => state.userPlaylist,
};

const { read } = getStoreAccessors<MainState, State>('');

export const readDashboardMiniDrawer = read(getters.dashboardMiniDrawer);
export const readDashboardShowDrawer = read(getters.dashboardShowDrawer);
export const readHasAdminAccess = read(getters.hasAdminAccess);
export const readIsLoggedIn = read(getters.isLoggedIn);
export const readLoginError = read(getters.loginError);
export const readToken = read(getters.token);
export const readUserProfile = read(getters.userProfile);
export const readFirstNotification = read(getters.firstNotification);
export const readSpotifyAuthCode = read(getters.spotifyAuthCode);
export const readSpotifyToken = read(getters.spotifyToken);
export const readRisingTracks = read(getters.risingTracks);
export const readCurrentTrack = read(getters.currentTrack);
export const readIsLoggedInSpotify = read(getters.isLoggedInSpotify);
export const readUserPlaylist = read(getters.userPlaylist);

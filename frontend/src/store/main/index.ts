import { mutations } from './mutations';
import { getters } from './getters';
import { actions } from './actions';
import { MainState } from './state';

const defaultState: MainState = {
  spotifyAuthCode: '',
  spotifyToken: null,
  isLoggedInSpotify: null,
  isLoggedIn: null,
  token: '',
  logInError: false,
  userProfile: null,
  dashboardMiniDrawer: false,
  dashboardShowDrawer: true,
  notifications: [],
  risingTracks: [],
  currentTrack: null,
  userPlaylist: {
    user_id: null,
    playlist_id: null,
    playlist_url: null,
    tracks: [],
  },
};

export const mainModule = {
  state: defaultState,
  mutations,
  actions,
  getters,
};

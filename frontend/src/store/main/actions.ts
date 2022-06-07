import { api } from '@/api';
import router from '@/router';
import {
  getLocalToken,
  removeLocalToken,
  saveLocalAuthCode,
  getLocalAuthCode,
  removeLocalAuthCode,
  saveLocalToken,
  getLocalSpotifyToken,
  getLocalSpotifyRefreshToken,
  getLocalSpotifyExpiresIn,
  getLocalSpotifyExpiresAt,
  spotifyTokenExpired,
  saveLocalSpotifyRefreshToken,
} from '@/utils';
import { spotifyScopes } from '../../env';
import { AxiosError } from 'axios';
import { getStoreAccessors } from 'typesafe-vuex';
import { ActionContext } from 'vuex';
import { State } from '../state';
import {
  commitAddNotification,
  commitRemoveNotification,
  commitSetLoggedInSpotify,
  commitSetSpotifyAuthCode,
  commitSetSpotifyToken,
  commitSetLoggedIn,
  commitSetLogInError,
  commitSetToken,
  commitSetUserProfile,
  commitSetRisingTracks,
  commitSetCurrentTrack,
  commitSetUserPlaylist,
} from './mutations';
import { AppNotification, MainState } from './state';
import {
  IRisingTrackParams,
  IUserProfileUpdate,
  IUserProfile,
} from '@/interfaces';

type MainContext = ActionContext<MainState, State>;

export const actions = {
  async actionLogIn(
    context: MainContext,
    payload: { username: string; password: string }
  ) {
    try {
      const response = await api.logInGetToken(
        payload.username,
        payload.password
      );
      const token = response.data.access_token;
      // console.log('Login Access Token: ', token);
      if (token) {
        saveLocalToken(token);
        commitSetToken(context, token);
        commitSetLoggedIn(context, true);
        commitSetLogInError(context, false);
        commitAddNotification(context, {
          content: 'Logged in',
          color: 'success',
        });
        // await dispatchCheckLoggedInSpotify(context);

        // dispatchGetRisingTracks(context, {
        //   params: {
        //     lag_days: 7,
        //     order_by: 'musicai_score',
        //     min_growth_rate: 0,
        //     max_growth_rate: 1e10,
        //     min_playcount: 0,
        //     max_playcount: 1e10,
        //     min_chg: 0,
        //     max_chg: 1e10,
        //     min_probability: 0.0,
        //     max_probability: 1.0,
        //     min_musicai_score: 0,
        //     max_musicai_score: 5,
        //     skip: 0,
        //     limit: 200,
        //   },
        // });
        await dispatchGetUserProfile(context);
        await dispatchRouteLoggedIn(context);
        commitAddNotification(context, {
          content: 'Logged in',
          color: 'success',
        });
      } else {
        await dispatchLogOut(context);
      }
    } catch (err) {
      commitSetLogInError(context, true);
      await dispatchLogOut(context);
    }
  },
  async actionLogInSpotify(context: MainContext) {
    // console.log('Inside dispatchLogInSpotify');
    try {
      const authCode = getLocalAuthCode();
      let spotifyToken = context.state.spotifyToken;
      let spotifyRefreshToken = getLocalSpotifyRefreshToken();
      let spotifyTokenExpiresAt = getLocalSpotifyExpiresAt();
      if (!spotifyToken) {
        const authURL = await api.spotifyGetAuthURL();
        // const auth_code = response.data.code;
        if (authURL) {
          // console.log(authURL);
          window.location.href = authURL;
          // window.open(authURL);
        }
      }
    } catch (err) {
      // TODO: handle errors
      // console.log('Error in dispatchLogInSpotify: ', err);
    }
  },
  async actionGetSpotifyToken(context: MainContext) {
    try {
      // console.log('Requesting Spotify Token from Code');
      const response = await api.spotifyGetToken(context.state.spotifyAuthCode);
      if (response.status === 200 && response.data) {
        let spotifyToken = response.data;
        commitSetSpotifyToken(context, spotifyToken);
        commitSetLoggedInSpotify(context, true);

        spotifyToken = context.state.spotifyToken;
        const userProfile: IUserProfile = context.state.userProfile;
        const spotifyProfile = await api.spotifyMe(spotifyToken.access_token);
        if (spotifyProfile) {
          // console.log(spotifyProfile);
          const spotifyID = spotifyProfile.id;
          if (spotifyID && !userProfile.spotify_id) {
            const updatedProfile: IUserProfileUpdate = {};
            updatedProfile.spotify_id = spotifyID;
            if (spotifyProfile.name && !userProfile.full_name) {
              updatedProfile.full_name = spotifyProfile.name;
            }
            // console.log(updatedProfile);
            await dispatchUpdateUserProfile(context, updatedProfile);
          }
        }
      } else if (response.status === 401) {
        // await dispatchRefreshSpotifyToken(context);
      }
    } catch (err) {
      // TODO: handle errors
      // console.log('Error in dispatchGetSpotifyToken: ', err);
      // await dispatchRefreshSpotifyToken(context);
    }
  },
  async actionRefreshSpotifyToken(context: MainContext) {
    try {
      // console.log('Requesting Spotify Token from Refresh Token Flow');
      let refreshToken = getLocalSpotifyRefreshToken();
      if (context.state.spotifyToken) {
        if (context.state.spotifyToken.refresh_token) {
          refreshToken = context.state.spotifyToken.refresh_token;
        }
      }
      // console.log('Passed RefreshToken: ', refreshToken);
      const response = await api.spotifyRefreshToken(refreshToken);
      if (response.status === 200 && response.data) {
        let spotifyToken = response.data;
        if (!spotifyToken.refresh_token) {
          spotifyToken.refresh_token = refreshToken;
        }
        commitSetSpotifyToken(context, spotifyToken);
        commitSetLoggedInSpotify(context, true);
        saveLocalSpotifyRefreshToken(spotifyToken.refresh_token);

        spotifyToken = context.state.spotifyToken;
        const userProfile: IUserProfile = context.state.userProfile;
        const spotifyProfile = await api.spotifyMe(spotifyToken.access_token);
        if (spotifyProfile) {
          // console.log(spotifyProfile);
          const spotifyID = spotifyProfile.id;
          if (spotifyID && !userProfile.spotify_id) {
            const updatedProfile: IUserProfileUpdate = {};
            updatedProfile.spotify_id = spotifyID;
            if (spotifyProfile.name && !userProfile.full_name) {
              updatedProfile.full_name = spotifyProfile.name;
            }
            // console.log(updatedProfile);
            await dispatchUpdateUserProfile(context, updatedProfile);
          }
        }
      }
    } catch (err) {
      // TODO: handle errors
      // console.log('Error in dispatchRefreshSpotifyToken: ', err);
      // await dispatchLogInSpotify(context);
    }
  },
  async actionGetUserProfile(context: MainContext) {
    try {
      const response = await api.getMe(context.state.token);
      if (response.data) {
        commitSetUserProfile(context, response.data);
      }
    } catch (error) {
      await dispatchCheckApiError(context, error);
    }
  },
  async actionUpdateUserProfile(context: MainContext, payload) {
    try {
      const loadingNotification = { content: 'saving', showProgress: true };
      commitAddNotification(context, loadingNotification);
      const response = (
        await Promise.all([
          api.updateMe(context.state.token, payload),
          await new Promise((resolve, reject) =>
            setTimeout(() => resolve(), 500)
          ),
        ])
      )[0];
      commitSetUserProfile(context, response.data);
      commitRemoveNotification(context, loadingNotification);
      commitAddNotification(context, {
        content: 'Profile successfully updated',
        color: 'success',
      });
    } catch (error) {
      await dispatchCheckApiError(context, error);
    }
  },
  async actionCheckLoggedIn(context: MainContext) {
    if (!context.state.isLoggedIn) {
      let token = context.state.token;
      if (!token) {
        const localToken = getLocalToken();
        if (localToken) {
          commitSetToken(context, localToken);
          token = localToken;
        }
      }
      if (token) {
        try {
          const response = await api.getMe(token);
          commitSetLoggedIn(context, true);
          commitSetUserProfile(context, response.data);
        } catch (error) {
          await dispatchRemoveLogIn(context);
        }
      } else {
        await dispatchRemoveLogIn(context);
      }
    }
  },
  async actionCheckLoggedInSpotify(context: MainContext) {
    let spotifyToken = context.state.spotifyToken;
    // console.log('Checking logged in Spotify: ', spotifyToken);
    if (!spotifyToken) {
      const token = getLocalSpotifyRefreshToken();
      // console.log('Local RefreshToken: ', token);
      if (token) {
        await dispatchRefreshSpotifyToken(context);
      } else {
        await dispatchLogInSpotify(context);
      }
      spotifyToken = context.state.spotifyToken;
    }

    // console.log(
    //   'Spotify Token expires at: ',
    //   spotifyToken.expires_at - Date.now()
    // );
    if (spotifyToken.expires_at) {
      if (spotifyTokenExpired(spotifyToken.expires_at)) {
        await dispatchRefreshSpotifyToken(context);
      }
    }
  },
  async actionRemoveLogIn(context: MainContext) {
    removeLocalToken();
    commitSetToken(context, '');
    commitSetLoggedIn(context, false);
  },
  async actionLogOut(context: MainContext) {
    await dispatchRemoveLogIn(context);
    await dispatchRouteLogOut(context);
  },
  async actionUserLogOut(context: MainContext) {
    await dispatchLogOut(context);
    commitAddNotification(context, { content: 'Logged out', color: 'success' });
  },
  actionRouteLogOut(context: MainContext) {
    if (router.currentRoute.path !== '/login') {
      router.push('/login');
    }
  },
  async actionCheckApiError(context: MainContext, payload: AxiosError) {
    if (payload.response!.status === 401) {
      await dispatchLogOut(context);
    }
  },
  actionRouteLoggedIn(context: MainContext) {
    if (
      router.currentRoute.path === '/login' ||
      router.currentRoute.path === '/'
    ) {
      router.push('/main');
    }
  },
  async removeNotification(
    context: MainContext,
    payload: { notification: AppNotification; timeout: number }
  ) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        commitRemoveNotification(context, payload.notification);
        resolve(true);
      }, payload.timeout);
    });
  },
  async passwordRecovery(context: MainContext, payload: { username: string }) {
    const loadingNotification = {
      content: 'Sending password recovery email',
      showProgress: true,
    };
    try {
      commitAddNotification(context, loadingNotification);
      const response = (
        await Promise.all([
          api.passwordRecovery(payload.username),
          await new Promise((resolve, reject) =>
            setTimeout(() => resolve(), 500)
          ),
        ])
      )[0];
      commitRemoveNotification(context, loadingNotification);
      commitAddNotification(context, {
        content: 'Password recovery email sent',
        color: 'success',
      });
      await dispatchLogOut(context);
    } catch (error) {
      commitRemoveNotification(context, loadingNotification);
      commitAddNotification(context, {
        color: 'error',
        content: 'Incorrect username',
      });
    }
  },
  async resetPassword(
    context: MainContext,
    payload: { password: string; token: string }
  ) {
    const loadingNotification = {
      content: 'Resetting password',
      showProgress: true,
    };
    try {
      commitAddNotification(context, loadingNotification);
      const response = (
        await Promise.all([
          api.resetPassword(payload.password, payload.token),
          await new Promise((resolve, reject) =>
            setTimeout(() => void resolve(), 500)
          ),
        ])
      )[0];
      commitRemoveNotification(context, loadingNotification);
      commitAddNotification(context, {
        content: 'Password successfully reset',
        color: 'success',
      });
      await dispatchLogOut(context);
    } catch (error) {
      commitRemoveNotification(context, loadingNotification);
      commitAddNotification(context, {
        color: 'error',
        content: 'Error resetting password',
      });
    }
  },
  async actionGetRisingTracks(
    context: MainContext,
    payload: { params: IRisingTrackParams }
  ) {
    try {
      const response = await api.getRisingTracks(
        context.rootState.main.token,
        payload.params
      );

      if (response) {
        commitSetRisingTracks(context, response.data);
        commitSetCurrentTrack(context, response.data[0]);
      }
    } catch (error) {
      await dispatchCheckApiError(context, error);
    }
  },
  async actionGetUserPlaylist(context: MainContext) {
    try {
      const response = await api.getUserPlaylist(
        context.rootState.main.token,
        context.rootState.main.spotifyToken.access_token
      );
      if (response) {
        commitSetUserPlaylist(context, response.data);
      }
    } catch (error) {
      await dispatchCheckApiError(context, error);
    }
  },
};

const { dispatch } = getStoreAccessors<MainState | any, State>('');

export const dispatchLogInSpotify = dispatch(actions.actionLogInSpotify);
export const dispatchCheckLoggedInSpotify = dispatch(
  actions.actionCheckLoggedInSpotify
);
export const dispatchGetSpotifyToken = dispatch(actions.actionGetSpotifyToken);
export const dispatchRefreshSpotifyToken = dispatch(
  actions.actionRefreshSpotifyToken
);
export const dispatchCheckApiError = dispatch(actions.actionCheckApiError);
export const dispatchCheckLoggedIn = dispatch(actions.actionCheckLoggedIn);
export const dispatchGetUserProfile = dispatch(actions.actionGetUserProfile);
export const dispatchLogIn = dispatch(actions.actionLogIn);
export const dispatchLogOut = dispatch(actions.actionLogOut);
export const dispatchUserLogOut = dispatch(actions.actionUserLogOut);
export const dispatchRemoveLogIn = dispatch(actions.actionRemoveLogIn);
export const dispatchRouteLoggedIn = dispatch(actions.actionRouteLoggedIn);
export const dispatchRouteLogOut = dispatch(actions.actionRouteLogOut);
export const dispatchUpdateUserProfile = dispatch(
  actions.actionUpdateUserProfile
);
export const dispatchRemoveNotification = dispatch(actions.removeNotification);
export const dispatchPasswordRecovery = dispatch(actions.passwordRecovery);
export const dispatchResetPassword = dispatch(actions.resetPassword);
export const dispatchGetRisingTracks = dispatch(actions.actionGetRisingTracks);
export const dispatchGetUserPlaylist = dispatch(actions.actionGetUserPlaylist);

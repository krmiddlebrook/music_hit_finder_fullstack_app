<template>
  <router-view></router-view>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { api } from '@/api';
import { store } from '@/store';
import {
  readLoginError,
  readUserProfile,
  readIsLoggedInSpotify,
  readSpotifyAuthCode,
  readSpotifyToken,
} from '@/store/main/getters';
import {
  dispatchLogInSpotify,
  dispatchGetSpotifyToken,
  dispatchRefreshSpotifyToken,
  dispatchUpdateUserProfile,
} from '@/store/main/actions';
import {
  commitSetLoggedInSpotify,
  commitSetSpotifyAuthCode,
  commitSetSpotifyToken,
} from '@/store/main/mutations';
import {
  appName,
  apiUrl,
  spotifyClientID,
  spotifyClientSecret,
  spotifyScopes,
  spotifyRedirectURI,
} from '@/env';
import {
  spotifyTokenExpired,
  saveLocalAuthCode,
  getLocalAuthCode,
} from '@/utils';
import { IUserProfileUpdate } from '@/interfaces';

const callbackRouteGuard = async (to, from, next) => {
  if (to.query.code) {
    // console.log('In SpotifyCallback, commiting spotify auth code');
    commitSetSpotifyAuthCode(store, to.query.code);
    saveLocalAuthCode(to.query.code);
    await dispatchGetSpotifyToken(store);
    // console.log('From route: ', from.path);
    // console.log('Next route: ', to.path);
    next(from.path);
  } else {
    next('/spotify-login');
  }

  //   if (readSpotifyToken(store)) {
  //     const token = readSpotifyToken(store);
  //     const hasExpired = spotifyTokenExpired(token.expires_at);
  //     // const timeRemaining = Math.floor((token.expires_at - Date.now()) / 1000);
  //     // console.log('Time until token expires (sec): ', timeRemaining);
  //     console.log('Token Expired: ', hasExpired);

  //     if (hasExpired === true) {
  //       dispatchRefreshSpotifyToken(store);
  //       console.log('Token Refreshed!');
  //       //   next('/main/rising-tracks');
  //     }
  //     next('/main/rising-tracks');
  //   } else {
  //     console.log('Bitch tits!');
  //     next();
  //   }
};

@Component
export default class SpotifyCallback extends Vue {
  public beforeRouteEnter(to, from, next) {
    callbackRouteGuard(to, from, next);
  }

  public beforeRouteUpdate(to, from, next) {
    callbackRouteGuard(to, from, next);
  }

  // created() {}
}
</script>

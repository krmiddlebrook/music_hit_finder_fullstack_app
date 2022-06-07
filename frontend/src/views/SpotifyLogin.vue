<template>
  <v-row cols="12" lg="12" md="12" sm="12" justify="center">
    <v-card class="elevation-12">
      <v-toolbar dark color="primary">
        <v-toolbar-title>Sign in to Spotify</v-toolbar-title>
      </v-toolbar>
      <v-card-actions>
        <v-btn class="ma-auto" @click="submit">Login</v-btn>
      </v-card-actions>
    </v-card>
  </v-row>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { api } from '@/api';
import { store } from '@/store';
import {
  readLoginError,
  readIsLoggedInSpotify,
  readSpotifyAuthCode,
  readSpotifyToken,
} from '@/store/main/getters';
import {
  dispatchLogInSpotify,
  dispatchGetSpotifyToken,
  dispatchRefreshSpotifyToken,
  dispatchCheckLoggedInSpotify,
} from '@/store/main/actions';
import {
  commitSetLoggedInSpotify,
  commitSetSpotifyAuthCode,
} from '@/store/main/mutations';
import axios from 'axios';
import querystring from 'querystring';
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

const spotifyRouteGuard = async (to, from, next) => {
  // await dispatchCheckLoggedInSpotify(store);
  // console.log('Spotify Logged In: ', readIsLoggedInSpotify(store));

  if (!readIsLoggedInSpotify(store) || readIsLoggedInSpotify(store) === false) {
    // console.log('Logging In!');
    next();
  } else {
    // console.log('Already Logged In!');
    next(from.path);
  }
};

@Component
export default class SpotifyLogin extends Vue {
  public beforeRouteEnter(to, from, next) {
    spotifyRouteGuard(to, from, next);
  }

  // public beforeRouteUpdate(to, from, next) {
  //   spotifyRouteGuard(to, from, next);
  // }

  public async submit() {
    try {
      await dispatchLogInSpotify(this.$store);
    } catch (err) {
      // console.log(err);
    }
  }
}
</script>

<style></style>

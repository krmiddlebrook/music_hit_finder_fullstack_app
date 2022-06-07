<template>
  <!-- <v-container fluid> -->
  <!-- <div> -->
  <!-- <v-row dense> -->
  <!-- <v-col cols="12"> -->
  <v-card>
    <v-card-title primary-title>
      <div class="headline primary--text">Dashboard</div>
    </v-card-title>
    <v-card-text>
      <div class="headline font-weight-light ma-5">
        Welcome {{ greetedUser }}
      </div>
    </v-card-text>
    <v-card-actions>
      <v-row dense>
        <v-btn to="/main/profile/view">View Profile</v-btn>
        <v-btn to="/main/profile/edit">Edit Profile</v-btn>
        <v-btn to="/main/profile/password" class="d-flex flex-wrap"
          ><span>Change Password</span></v-btn
        >
        <v-btn v-show="!loggedInSpotify" @click="spotifyLogin">
          Spotify Login
        </v-btn>
        <v-btn
          to="/main/playlist"
          color="grey lighten-2"
          class="elevation-1 ma-auto"
          icon
        >
          <v-icon>mdi-play</v-icon>
        </v-btn>
      </v-row>
    </v-card-actions>
  </v-card>
  <!-- </v-col> -->
  <!-- </v-row> -->
  <!-- </div> -->
  <!-- </v-container> -->
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { Store } from 'vuex';
import { IUserProfileUpdate } from '@/interfaces';
import {
  readUserProfile,
  readToken,
  readSpotifyToken,
  readIsLoggedInSpotify,
} from '@/store/main/getters';
import {
  dispatchLogInSpotify,
  dispatchCheckLoggedInSpotify,
  dispatchUpdateUserProfile,
} from '@/store/main/actions';
import {
  commitAddNotification,
  commitRemoveNotification,
} from '../../store/main/mutations';
import { api } from '../../api';

@Component
export default class Dashboard extends Vue {
  public get greetedUser() {
    const userProfile = readUserProfile(this.$store);
    if (userProfile) {
      if (userProfile.full_name) {
        return userProfile.full_name;
      } else {
        return userProfile.email;
      }
    }
  }

  public get loggedInSpotify() {
    return readIsLoggedInSpotify(this.$store);
  }

  public async spotifyLogin() {
    await dispatchLogInSpotify(this.$store);
  }

  // TODO: move this to a new view when finished testing
  public async createUserPlaylist() {
    // console.log('Can the spotify profile work please!: ');
    await dispatchCheckLoggedInSpotify(this.$store);

    const spotifyToken = readSpotifyToken(this.$store);
    // console.log(spotifyToken);
    const userToken = readToken(this.$store);
    const userProfile = readUserProfile(this.$store);
    const spotifyProfile = await api.spotifyMe(spotifyToken.access_token);
    console.log('Spotify Profile: ', spotifyProfile);
    if (spotifyProfile) {
      // console.log(spotifyProfile);
      const spotifyID = spotifyProfile.id;
      if (spotifyID) {
        const updatedProfile: IUserProfileUpdate = {};
        updatedProfile.spotify_id = spotifyID;
        if (!userProfile.full_name && spotifyProfile.name) {
          updatedProfile.full_name = spotifyProfile.name;
        }
        // console.log(updatedProfile);
        await dispatchUpdateUserProfile(this.$store, updatedProfile);
      }
    }
    const loadingNotification = {
      content: 'Baking your MusicAI Playlist',
      showProgress: true,
    };
    commitAddNotification(this.$store, loadingNotification);
    const userPlaylist = await api.getUserPlaylist(
      userToken,
      spotifyToken.access_token
    );
    commitRemoveNotification(this.$store, loadingNotification);
    const successNotification = {
      content: 'Your playlist is ready. Enjoy. Check your Spotify.',
      showProgress: false,
      color: 'success',
    };
    commitAddNotification(this.$store, successNotification);
    commitRemoveNotification(this.$store, successNotification);
    // console.log('Custom User Playlist created: ', userPlaylist);
    this.$router.push('/main/playlist');
  }
}
</script>

<template>
  <!-- <v-container fluid> -->
  <v-row dense>
    <v-col cols="12">
      <!-- <v-card>
          <v-progress-linear
            :active="loading"
            :indeterminate="loading"
            absolute
            bottom
            color="deep-purple accent-4"
          ></v-progress-linear>
        </v-card> -->

      <v-card>
        <v-progress-linear
          :active="loading"
          :indeterminate="loading"
          absolute
          bottom
          color="deep-purple accent-4"
        ></v-progress-linear>
        <!-- </v-card> -->
        <v-card-title>
          Your MusicAI Mix
        </v-card-title>
        <v-card-subtitle
          >A playlist created just for you of the hottest new music (updated
          weekly). Enjoy!</v-card-subtitle
        >

        <v-container fluid>
          <v-row dense>
            <v-col
              v-for="track in userPlaylist.tracks"
              :key="track.id"
              cols="12"
            >
              <v-card>
                <div class="d-flex flex-wrap align-center">
                  <v-avatar tile size="70">
                    <v-img
                      alt="album cover"
                      :src="track.album.images.slice(-1)[0].url"
                      contain
                    ></v-img>
                  </v-avatar>

                  <v-btn icon class="elevation-1 mx-2">
                    <v-icon color="grey lighten-1">mdi-play</v-icon>
                  </v-btn>

                  <div>
                    <v-card-title
                      class="headline"
                      v-text="track.name"
                    ></v-card-title>

                    <v-card-subtitle
                      v-text="artistStr(track)"
                    ></v-card-subtitle>
                  </div>
                </div>
              </v-card>
            </v-col>
          </v-row>
        </v-container>
      </v-card>
    </v-col>
  </v-row>
  <!-- </v-container> -->
</template>

<script lang="ts">
import { Component, Vue, Prop, Watch } from 'vue-property-decorator';
import { Store } from 'vuex';
import { IUserProfileUpdate } from '@/interfaces';
import {
  readUserProfile,
  readToken,
  readSpotifyToken,
  readUserPlaylist,
} from '@/store/main/getters';
import {
  dispatchLogInSpotify,
  dispatchCheckLoggedInSpotify,
  dispatchUpdateUserProfile,
  dispatchGetUserPlaylist,
} from '@/store/main/actions';
import {
  commitAddNotification,
  commitRemoveNotification,
} from '../../store/main/mutations';
import { api } from '../../api';
import { trackArtists } from '../../utils';

@Component
export default class Dashboard extends Vue {
  public loading = true;

  public get userPlaylist() {
    const uPlaylist = readUserPlaylist(this.$store);
    if (uPlaylist.tracks.length > 0 || uPlaylist.playlist_id) {
      this.loading = false;
    }
    return uPlaylist;
  }

  public artistStr(track) {
    return trackArtists(track);
  }

  public async created() {
    if (this.userPlaylist.tracks.length === 0) {
      await dispatchCheckLoggedInSpotify(this.$store);
      await dispatchGetUserPlaylist(this.$store);
      this.loading = false;
    }
  }
}
</script>

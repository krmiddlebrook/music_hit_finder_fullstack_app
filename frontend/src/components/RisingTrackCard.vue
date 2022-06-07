<template>
  <v-hover v-slot="{ hover }">
    <v-card
      :elevation="hover ? 16 : 2"
      class="primary-grad"
      min-width="215"
      max-width="1400"
    >
      <div class="d-flex flex-wrap align-center">
        <v-avatar tile size="100" class="pl-1">
          <v-img alt="album cover" :src="albumCover" contain></v-img>
        </v-avatar>

        <div>
          <v-card-title
            class="headline font-weight-bold"
            v-text="track.name"
          ></v-card-title>
          <v-card-subtitle
            class="font-weight-medium text--secondary"
            v-text="track.artists_str"
          ></v-card-subtitle>
        </div>

        <v-tooltip right>
          <template v-slot:activator="{ on, attrs }">
            <div v-bind="attrs" v-on="on">
              <v-rating
                :value="track.musicai_score"
                empty-icon="mdi-star-outline"
                full-icon="mdi-star"
                half-icon="mdi-star-half-full"
                length="5"
                size="25"
                color="gold darken-1"
                background-color="gold darken-1"
                readonly
              ></v-rating>
            </div>
          </template>
          <span>MusicAI Score&trade;</span>
        </v-tooltip>

        <v-col cols="12" class="ma-0 pa-1">
          <v-divider></v-divider>

          <v-card-actions>
            <v-btn
              @click="playTrack"
              color="grey lighten-2"
              class="elevation-1"
              icon
            >
              <v-icon fab>{{ playButton }}</v-icon>
            </v-btn>

            <v-tooltip bottom>
              <template v-slot:activator="{ on, attrs }">
                <v-btn
                  color="grey lighten-2"
                  v-bind="attrs"
                  v-on="on"
                  @click="saveTrack"
                  class="ml-1 mr-2 elevation-1"
                  icon
                >
                  <v-icon fab>mdi-bookmark-outline</v-icon>
                </v-btn>
              </template>
              <span>Save to library</span>
            </v-tooltip>

            <v-spacer></v-spacer>

            <v-chip-group column>
              <v-chip
                :color="
                  sortBy === 'Growth Rate' ? '#8026a6b2' : 'grey darken-3'
                "
                label
                ><span
                  class="text-lg-h6 text-md-h6 text-sm-body-1 font-weight-medium"
                >
                  Growth: {{ prettyGrowthRate }}
                </span>
              </v-chip>

              <v-chip
                label
                :color="sortBy === 'Playcount' ? '#8026a6b2' : 'grey darken-3'"
                ><span
                  class="text-lg-h6 text-md-h6 text-sm-body-1 font-weight-medium"
                >
                  Plays: {{ prettyPlaycount }}
                </span>
              </v-chip>

              <v-chip
                label
                :color="sortBy === 'Change' ? '#8026a6b2' : 'grey darken-3'"
              >
                <span
                  class="text-lg-h6 text-md-h6 text-sm-body-1 font-weight-medium"
                >
                  Change : {{ prettyChange }}
                </span>
              </v-chip>
            </v-chip-group>
          </v-card-actions>
        </v-col>

        <!-- <div class="d-flex flex-wrap align-center">
          <v-card-actions>
            <v-btn
              @click="playTrack"
              color="grey lighten-2"
              class="elevation-1"
              icon
            >
              <v-icon fab>{{ playButton }}</v-icon>
            </v-btn>

            <v-tooltip bottom>
              <template v-slot:activator="{ on, attrs }">
                <v-btn
                  color="grey lighten-2"
                  v-bind="attrs"
                  v-on="on"
                  @click="saveTrack"
                  class="ml-1 mr-2 elevation-1"
                  icon
                >
                  <v-icon fab>mdi-bookmark-outline</v-icon>
                </v-btn>
              </template>
              <span>Save to library</span>
            </v-tooltip>

            <v-spacer></v-spacer>

            <v-chip-group column>
              <v-chip
                :color="
                  sortBy === 'Growth Rate' ? '#8026a6b2' : 'grey darken-3'
                "
                label
                ><span
                  class="text-lg-h6 text-md-h6 text-sm-body-1 font-weight-medium"
                >
                  Growth: {{ prettyGrowthRate }}
                </span>
              </v-chip>

              <v-chip
                label
                :color="sortBy === 'Playcount' ? '#8026a6b2' : 'grey darken-3'"
                ><span
                  class="text-lg-h6 text-md-h6 text-sm-body-1 font-weight-medium"
                >
                  Plays: {{ prettyPlaycount }}
                </span>
              </v-chip>

              <v-chip
                label
                :color="sortBy === 'Change' ? '#8026a6b2' : 'grey darken-3'"
              >
                <span
                  class="text-lg-h6 text-md-h6 text-sm-body-1 font-weight-medium"
                >
                  Change : {{ prettyChange }}
                </span>
              </v-chip>
            </v-chip-group>
          </v-card-actions>
        </div> -->

        <!-- TODO: feature to share this track to socials -->
        <!-- <v-dialog v-model="dialog" width="400">
                  <template v-slot:activator="{ on }">
                    <v-icon v-on="on">
                      mdi-share-variant
                    </v-icon>
                  </template>
                  <v-card>
                    <v-card-title>
                      <span class="title font-weight-bold">Share</span>
                      <v-spacer></v-spacer>
                      <v-btn class="mx-0" icon @click="dialog = false">
                        <v-icon>mdi-close-circle-outline</v-icon>
                      </v-btn>
                    </v-card-title>
                    <v-list>
                      <v-list-item>
                        <v-list-item-action>
                          <v-icon color="indigo">
                            mdi-facebook
                          </v-icon>
                        </v-list-item-action>
                        <v-card-title>Facebook</v-card-title>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-action>
                          <v-icon color="cyan">
                            mdi-twitter
                          </v-icon>
                        </v-list-item-action>
                        <v-card-title>Twitter</v-card-title>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-action>
                          <v-icon>mdi-email</v-icon>
                        </v-list-item-action>
                        <v-card-title>Email</v-card-title>
                      </v-list-item>
                    </v-list>
                    <v-text-field
                      :label="copied ? 'Link copied' : 'Click to copy link'"
                      class="pa-4"
                      readonly
                      :value="link"
                      @click="copyLink"
                    ></v-text-field>
                  </v-card>
                </v-dialog> -->

        <!-- <v-card-actions>
                  <v-btn icon>
                    <v-icon>mdi-share-variant</v-icon>
                  </v-btn>
                </v-card-actions> -->
      </div>
    </v-card>
  </v-hover>
</template>

<script lang="ts">
import { Component, Vue, Prop, Emit, Watch } from 'vue-property-decorator';
import { Store } from 'vuex';
import { IRisingTrack } from '../interfaces';
import {
  formatPlaycount,
  formatGrowthRate,
  formatChange,
  titleCase,
} from '../utils';
import {
  readCurrentTrack,
  readSpotifyToken,
  readIsLoggedInSpotify,
  readToken,
} from '../store/main/getters';
import { dispatchCheckLoggedInSpotify } from '../store/main/actions';
import { commitSetCurrentTrack } from '../store/main/mutations';
import { api } from '../api';

@Component
export default class RisingTrackCard extends Vue {
  @Prop() track: IRisingTrack | undefined;
  @Prop({ default: '' }) sortBy: string | undefined;
  @Prop({ default: 'mdi-play' }) playButton: string;
  @Prop({ default: 0 }) progress: number;

  // computed
  public get prettyPlaycount() {
    return formatPlaycount(this.track.playcount);
  }

  public get prettyGrowthRate() {
    return formatGrowthRate(this.track.growth_rate);
  }

  public get prettyChange() {
    return formatChange(this.track.chg);
  }

  public get trackGenres() {
    const artists = this.track.artists.filter((art) => {
      if (art.genres) {
        if (art.genres.length > 0) {
          return art;
        }
      }
    });
    const genres = artists.map((art) => {
      const art_genres = art.genres.map((g) => titleCase(g.id));
      return art_genres.join(', ');
    });
    return genres.join(', ');
  }

  public get albumCover() {
    if (this.track.album.cover) {
      return this.track.album.cover;
    } else {
      return 'https://i.redd.it/t7gytb60d9j11.jpg';
    }
  }

  // methods
  public playTrack() {
    this.$emit('play-track', this.track);
  }

  public async saveTrack() {
    await dispatchCheckLoggedInSpotify(this.$store);
    if (readIsLoggedInSpotify(this.$store) === true) {
      const track_id = this.track.track.id;
      const spotifyToken = readSpotifyToken(this.$store);
      // console.log(spotifyToken);
      const trackSaved = await api.saveTrack(
        spotifyToken.access_token,
        track_id
      );
      console.log('Track saved: ', trackSaved);
    } else {
      this.$router.push('/spotify-login');
    }
  }

  // TODO: graph of playcount history on expand
}
</script>

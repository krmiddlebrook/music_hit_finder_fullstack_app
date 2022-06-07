<template>
  <!-- <div> -->
  <v-data-iterator
    :items="risingTracks"
    :items-per-page.sync="itemsPerPage"
    item-key="id"
    :page="page"
    :search="search"
    :sort-by="sortBy"
    :sort-desc="sortDesc"
    :loading="loading"
    loading-text="Retrieving Rising Tracks for You!"
    disable-pagination
    hide-default-footer
  >
    <template v-slot:header>
      <Navbar :expandOnHover="$vuetify.breakpoint.mobile">
        <template v-slot:app-bar-extension>
          <template v-if="!$vuetify.breakpoint.mobile">
            <div class="d-flex justify-space-around">
              <div class="mx-2">
                <v-text-field
                  v-model="search"
                  prepend-inner-icon="mdi-magnify"
                  label="Search"
                  clearable
                  flat
                  solo-inverted
                  hide-details
                ></v-text-field>
              </div>

              <div class="mx-2">
                <v-select
                  v-model="sortBy"
                  :items="sortLabels"
                  prepend-inner-icon="mdi-arrow-up"
                  label="Sort by"
                  flat
                  solo-inverted
                  hide-details
                ></v-select>
              </div>

              <div class="mx-2">
                <v-select
                  v-model="lag_days"
                  :items="lagDayOptions"
                  prepend-inner-icon="mdi-calendar"
                  label="Period:"
                  flat
                  solo-inverted
                  hide-details
                ></v-select>
              </div>

              <v-spacer></v-spacer>

              <div class="mx-2">
                <v-btn-toggle v-model="sortDesc">
                  <v-btn depressed color="purple darken-3" :value="false">
                    <v-icon>mdi-arrow-up</v-icon>
                  </v-btn>
                  <v-btn depressed color="purple darken-3" :value="true">
                    <v-icon>mdi-arrow-down</v-icon>
                  </v-btn>
                </v-btn-toggle>
              </div>
            </div>

            <v-progress-linear
              :active="loading"
              :indeterminate="loading"
              absolute
              bottom
              color="deep-purple accent-1"
            ></v-progress-linear>
          </template>
          <template v-else>
            <v-menu bottom :close-on-content-click="false">
              <template v-slot:activator="{ on, attrs }">
                <v-btn icon v-bind="attrs" v-on="on">
                  <v-icon>mdi-magnify</v-icon>
                </v-btn>
              </template>

              <v-list>
                <v-list-item>
                  <v-list-item-title>
                    <v-text-field
                      v-model="search"
                      prepend-inner-icon="mdi-magnify"
                      label="Search"
                      clearable
                      flat
                      solo-inverted
                      hide-details
                    ></v-text-field>
                  </v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>

            <v-menu bottom :close-on-content-click="false">
              <template v-slot:activator="{ on, attrs }">
                <v-btn icon v-bind="attrs" v-on="on">
                  <v-icon>mdi-arrow-up</v-icon>
                </v-btn>
              </template>

              <v-list>
                <v-list-item>
                  <v-list-item-title>
                    <v-select
                      v-model="sortBy"
                      :items="sortLabels"
                      label="Sort by"
                      flat
                      solo-inverted
                      hide-details
                    ></v-select>
                  </v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>

            <v-menu bottom :close-on-content-click="false">
              <template v-slot:activator="{ on, attrs }">
                <v-btn icon v-bind="attrs" v-on="on">
                  <v-icon>mdi-calendar</v-icon>
                </v-btn>
              </template>

              <v-list>
                <v-list-item>
                  <v-list-item-title>
                    <v-select
                      v-model="lag_days"
                      :items="lagDayOptions"
                      label="Period:"
                      flat
                      solo-inverted
                      hide-details
                    ></v-select>
                  </v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>

            <!-- Filters -->
            <v-menu right bottom>
              <template v-slot:activator="{ on, attrs }">
                <v-btn icon v-bind="attrs" v-on="on">
                  <v-icon>mdi-dots-vertical</v-icon>
                </v-btn>
              </template>

              <v-list dense>
                <v-list-item>
                  <v-switch v-model="autoplay"></v-switch>
                  <v-list-item-content>
                    <v-list-item-title v-text="'Autoplay'"></v-list-item-title>
                  </v-list-item-content>
                </v-list-item>

                <v-subheader>Filters</v-subheader>

                <v-list-item>
                  <v-list-item-content>
                    <v-list-item-title
                      v-text="'Growth Rate (%)'"
                    ></v-list-item-title>
                    <v-col cols="12">
                      <vue-slider
                        v-model="growthRateTick"
                        :data="growthRateTickMarks"
                        :marks="true"
                        :tooltip="'active'"
                        :lazy="true"
                        :absorb="true"
                        :enable-cross="false"
                        :contained="true"
                        :hide-label="true"
                      ></vue-slider>
                    </v-col>
                  </v-list-item-content>
                </v-list-item>

                <v-list-item>
                  <v-list-item-content>
                    <v-list-item-title v-text="'Playcount'"></v-list-item-title>
                    <v-col cols="12">
                      <vue-slider
                        v-model="playcountTick"
                        :data="playcountTickMarks"
                        :marks="true"
                        :tooltip="'active'"
                        :lazy="true"
                        :absorb="true"
                        :enable-cross="false"
                        :contained="true"
                        :hide-label="true"
                      ></vue-slider>
                    </v-col>
                  </v-list-item-content>
                </v-list-item>

                <v-list-item>
                  <v-list-item-content>
                    <v-list-item-title v-text="'Change'"></v-list-item-title>
                    <v-col cols="12">
                      <vue-slider
                        v-model="changeTick"
                        :data="changeTickMarks"
                        :marks="true"
                        :tooltip="'active'"
                        :lazy="true"
                        :absorb="true"
                        :enable-cross="false"
                        :contained="true"
                        :hide-label="true"
                      ></vue-slider>
                    </v-col>
                  </v-list-item-content>
                </v-list-item>

                <v-list-item>
                  <v-list-item-content>
                    <v-list-item-title
                      v-text="'MusicAI Score'"
                    ></v-list-item-title>
                    <v-col cols="12">
                      <vue-slider
                        v-model="musicaiScoreTick"
                        :data="musicaiScoreTickMarks"
                        :marks="true"
                        :tooltip="'active'"
                        :lazy="true"
                        :absorb="true"
                        :enable-cross="false"
                        :contained="true"
                        :hide-label="true"
                      ></vue-slider>
                    </v-col>
                  </v-list-item-content>
                </v-list-item>
              </v-list>
            </v-menu>

            <v-progress-linear
              :active="loading"
              :indeterminate="loading"
              absolute
              bottom
              color="deep-purple accent-1"
            ></v-progress-linear>
          </template>
          <!-- </v-app-bar> -->
        </template>

        <!-- <template v-slot:more>
            <template v-if="!$vuetify.breakpoint.mobile">
              <v-list dense>
                <v-list-item>
                  <v-list-item-content>
                    <v-col>
                      <span class="caption ma-auto">Autoplay</span>
                      <v-switch
                        dense
                        v-model="autoplay"
                        class="ma-auto"
                      ></v-switch>
                    </v-col>
                  </v-list-item-content>
                </v-list-item>

                <v-list-item>
                  <v-list-item-content>
                    <v-col>
                      <span class="caption ma-auto">Growth Rate (%)</span>
                      <vue-slider
                        v-model="growthRateTick"
                        :data="growthRateTickMarks"
                        :marks="true"
                        :tooltip="'none'"
                        :lazy="true"
                        :absorb="true"
                        :enable-cross="false"
                      ></vue-slider>
                    </v-col>
                  </v-list-item-content>
                </v-list-item>

                <v-list-item>
                  <v-list-item-content>
                    <v-col>
                      <span class="caption ma-auto">Playcount</span>
                      <vue-slider
                        v-model="playcountTick"
                        :data="playcountTickMarks"
                        :marks="true"
                        :tooltip="'none'"
                        :lazy="true"
                        :absorb="true"
                        :enable-cross="false"
                      ></vue-slider>
                    </v-col>
                  </v-list-item-content>
                </v-list-item>

                <v-list-item>
                  <v-list-item-content>
                    <v-col>
                      <span class="caption ma-auto">Change</span>
                      <vue-slider
                        v-model="changeTick"
                        :data="changeTickMarks"
                        :marks="true"
                        :tooltip="'none'"
                        :lazy="true"
                        :absorb="true"
                        :enable-cross="false"
                      ></vue-slider>
                    </v-col>
                  </v-list-item-content>
                </v-list-item>

                <v-list-item>
                  <v-list-item-content>
                    <v-col>
                      <span class="caption ma-auto">MusicAI Score</span>
                      <vue-slider
                        v-model="musicaiScoreTick"
                        :data="musicaiScoreTickMarks"
                        :marks="true"
                        :tooltip="'none'"
                        :lazy="true"
                        :absorb="true"
                        :enable-cross="false"
                      ></vue-slider>
                    </v-col>
                  </v-list-item-content>
                </v-list-item>
              </v-list>
            </template>
          </template> -->
      </Navbar>
    </template>

    <!-- Tracks -->
    <template v-slot:default="props">
      <v-row dense class="fill-height">
        <!-- Filters -->
        <template v-if="!$vuetify.breakpoint.mobile">
          <v-card cols="4">
            <v-list dense>
              <v-list-item>
                <v-switch v-model="autoplay"></v-switch>
                <v-list-item-content>
                  <v-list-item-title v-text="'Autoplay'"></v-list-item-title>
                </v-list-item-content>
              </v-list-item>

              <v-subheader>Filters</v-subheader>

              <v-list-item>
                <v-list-item-content>
                  <v-list-item-title
                    v-text="'Growth Rate (%)'"
                  ></v-list-item-title>
                  <v-col cols="12">
                    <vue-slider
                      v-model="growthRateTick"
                      :data="growthRateTickMarks"
                      :marks="true"
                      :tooltip="'active'"
                      :lazy="true"
                      :absorb="true"
                      :enable-cross="false"
                      :contained="true"
                      :hide-label="true"
                    ></vue-slider>
                  </v-col>
                </v-list-item-content>
              </v-list-item>

              <v-list-item>
                <v-list-item-content>
                  <v-list-item-title v-text="'Playcount'"></v-list-item-title>
                  <v-col cols="12">
                    <vue-slider
                      v-model="playcountTick"
                      :data="playcountTickMarks"
                      :marks="true"
                      :tooltip="'active'"
                      :lazy="true"
                      :absorb="true"
                      :enable-cross="false"
                      :contained="true"
                      :hide-label="true"
                    ></vue-slider>
                  </v-col>
                </v-list-item-content>
              </v-list-item>

              <v-list-item>
                <v-list-item-content>
                  <v-list-item-title v-text="'Change'"></v-list-item-title>
                  <v-col cols="12">
                    <vue-slider
                      v-model="changeTick"
                      :data="changeTickMarks"
                      :marks="true"
                      :tooltip="'active'"
                      :lazy="true"
                      :absorb="true"
                      :enable-cross="false"
                      :contained="true"
                      :hide-label="true"
                    ></vue-slider>
                  </v-col>
                </v-list-item-content>
              </v-list-item>

              <v-list-item>
                <v-list-item-content>
                  <v-list-item-title
                    v-text="'MusicAI Score'"
                  ></v-list-item-title>
                  <v-col cols="12">
                    <vue-slider
                      v-model="musicaiScoreTick"
                      :data="musicaiScoreTickMarks"
                      :marks="true"
                      :tooltip="'active'"
                      :lazy="true"
                      :absorb="true"
                      :enable-cross="false"
                      :contained="true"
                      :hide-label="true"
                    ></vue-slider>
                  </v-col>
                </v-list-item-content>
              </v-list-item>
            </v-list>
          </v-card>
        </template>

        <v-col cols="8">
          <v-col
            v-for="item in props.items"
            :key="item.id"
            cols="12"
            class="ma-auto"
          >
            <!-- <v-container class="mx-lg-auto"> -->
            <!-- <v-row dense> -->
            <!-- <v-col cols="12"> -->
            <!-- <v-list> -->

            <!-- <v-list-item v-for="item in props.items" :key="item.id"> -->
            <!-- <v-list-item-content> -->
            <rising-track-card
              :track="item"
              :key="item.id"
              :sortBy="sortBy"
              :playButton="playPauseButton(item)"
              :progress="trackProgress(item)"
              @play-track="toggleTrack"
            ></rising-track-card>
            <!-- </v-list-item-content> -->
            <!-- </v-list-item> -->
            <!-- </v-list> -->
          </v-col>
        </v-col>
      </v-row>
    </template>
  </v-data-iterator>
  <!-- </div> -->
</template>

<script lang="ts">
import { Component, Vue, Watch } from 'vue-property-decorator';
import VueSlider from 'vue-slider-component';
import 'vue-slider-component/theme/material.css';
import { Store } from 'vuex';
import arraySort from 'array-sort';
import {
  readRisingTracks,
  readCurrentTrack,
  readSpotifyToken,
} from '@/store/main/getters';
import {
  commitSetCurrentTrack,
  commitSetRisingTracks,
} from '@/store/main/mutations';
import {
  dispatchGetRisingTracks,
  dispatchUserLogOut,
} from '@/store/main/actions';
import {
  IRisingTrack,
  ITrack,
  ITrackPlay,
  IRisingTrackParams,
} from '../../interfaces';
import { formatPlaycount, formatGrowthRate, formatChange } from '@/utils';
import RisingTrackCard from '../../components/RisingTrackCard.vue';
import Navbar from '../../components/Navbar.vue';
import { api } from '@/api';

//TODO: create component for rising track card, will enable caching

@Component({
  components: {
    Navbar,
    VueSlider,
    RisingTrackCard,
  },
})
export default class RisingTracks extends Vue {
  itemsPerPage = 200;
  search = '';
  sortBy = '';
  sortDesc = true;
  sortLabels = ['Playcount', 'Change', 'Growth Rate', 'MusicAI Score'];
  labels2keys = {
    Playcount: 'playcount',
    Change: 'chg',
    'Growth Rate': 'growth_rate',
    'MusicAI Score': 'probability',
  };
  page: number = 1;
  isPlaying: boolean = false;
  index: number = 0;
  currentProgress: number = 0;
  autoplay: boolean = true;
  infinitySymbol: string = '∞';
  infinityValue: number = 1e10;

  growthRateTickMarks = {
    '0': 0,
    '50': 50,
    '100': 100,
    '500': 500,
    '1k': 1000,
    '∞': this.infinityValue,
  };
  growthRateTick = ['0', this.infinitySymbol];

  playcountTickMarks = {
    '0': 0,
    '10k': 1e4,
    '50k': 5e4,
    '100k': 1e5,
    '500k': 5e5,
    '1m': 1e6,
    '5m': 1e6,
    '10m': 1e7,
    '∞': this.infinityValue,
  };
  playcountTick = ['10k', this.infinitySymbol];

  changeTickMarks = {
    '0': 0,
    '1k': 1e3,
    '10k': 1e4,
    '100k': 1e5,
    '500k': 5e5,
    '1m': 1e6,
    '∞': this.infinityValue,
  };
  changeTick = ['1k', this.infinitySymbol];

  musicaiScoreTickMarks = [1, 2, 3, 4, 5];
  musicaiScoreTick = [0, 5];

  // API Rising Tracks Params
  lag_days: number = 7;
  lagDayOptions = [7, 15, 30];
  order_by: string = 'musicai_score';
  min_probability: number = 0.0;
  max_probability: number = 1.0;
  skip: number = 0;
  limit: number = 200;

  public loading = false;

  // dialog = false;
  // copied = false;
  // link = 'http://localhost:8080/main/rising-tracks';

  /* computed operations */
  public get queryParams(): IRisingTrackParams {
    return {
      lag_days: this.lag_days,
      order_by: this.order_by,
      min_growth_rate: this.growthRateTickMarks[this.growthRateTick[0]],
      max_growth_rate: this.growthRateTickMarks[this.growthRateTick[1]],
      min_playcount: this.playcountTickMarks[this.playcountTick[0]],
      max_playcount: this.playcountTickMarks[this.playcountTick[1]],
      min_chg: this.changeTickMarks[this.changeTick[0]],
      max_chg: this.changeTickMarks[this.changeTick[1]],
      min_probability: this.min_probability,
      max_probability: this.max_probability,
      min_musicai_score: this.musicaiScoreTick[0],
      max_musicai_score: this.musicaiScoreTick[1],
      skip: this.skip,
      limit: this.limit,
    };
  }

  public get risingTracks(): IRisingTrack[] {
    let tracks = readRisingTracks(this.$store);
    tracks = tracks.map((t) => {
      t.player.onended = () => {
        if (this.autoplay) {
          this.currentProgress = 0;
          this.next(this.index);
        }
      };
      return t;
    });

    tracks = tracks.filter((t) => {
      return (
        this.playcountTickMarks[this.playcountTick[0]] <= t.playcount &&
        t.playcount <= this.playcountTickMarks[this.playcountTick[1]] &&
        this.growthRateTickMarks[this.growthRateTick[0]] <= t.growth_rate &&
        t.growth_rate * 100 <=
          this.growthRateTickMarks[this.growthRateTick[1]] &&
        this.changeTickMarks[this.changeTick[0]] <= t.chg &&
        t.chg <= this.changeTickMarks[this.changeTick[1]] &&
        this.musicaiScoreTick[0] <= t.musicai_score &&
        t.musicai_score <= this.musicaiScoreTick[1]
      );
    });

    return arraySort(tracks, this.labels2keys[this.sortBy], {
      reverse: this.sortDesc,
    });
    this.itemsPerPage = tracks.length;
  }

  public get itemsPerPageArray() {
    const total_tracks = this.risingTracks.length;
    return [25, 50, total_tracks];
  }

  public get numberOfPages() {
    return Math.ceil(this.risingTracks.length / this.itemsPerPage);
  }

  public get currentTrack(): IRisingTrack {
    return readCurrentTrack(this.$store);
  }

  public set currentTrack(track: IRisingTrack) {
    commitSetCurrentTrack(this.$store, track);
    this.index = this.risingTracks.indexOf(this.currentTrack);
  }

  /*  methods   */
  public isCurrentTrack(track: IRisingTrack) {
    if (this.currentTrack) {
      return track.id === this.currentTrack.id ? true : false;
    } else {
      return false;
    }
  }

  public pause(): void {
    this.currentTrack.player.pause();
    this.pauseListener();
    this.isPlaying = false;
    // console.log('Track paused');
  }

  public play(): void {
    this.currentTrack.player.play();
    this.isPlaying = true;
    this.currentTrack.player.addEventListener(
      'timeupdate',
      this.playbackListener
    );
    // console.log('Track playing');
  }

  public toggleTrack(track: IRisingTrack) {
    const isSameTrack = this.isCurrentTrack(track);
    if (isSameTrack === false) {
      // Pause the current playing track
      this.pause();
      this.currentTrack = track;
      // Play the new track
      this.play();
    } else if (this.isPlaying) {
      // Pause the current playing track
      this.pause();
    } else {
      // Unpause the current track
      this.play();
    }
  }

  public playPauseButton(item: IRisingTrack): string {
    const itemIsCurrent = this.isCurrentTrack(item);
    if (this.isPlaying && itemIsCurrent) {
      return 'mdi-pause';
    } else {
      return 'mdi-play';
    }
  }

  public trackProgress(item: IRisingTrack): number {
    const itemIsCurrent = this.isCurrentTrack(item);
    if (itemIsCurrent) {
      // console.log('Current Progress: ', this.currentProgress);
      return this.currentProgress;
    } else {
      return 0;
    }
  }

  // Playback listener function runs every 100ms while player is playing
  public playbackListener(e): void {
    // Sync local 'currentProgress' to this.currentTrack.player.currentTime and
    // update global state
    this.currentProgress =
      (this.currentTrack.player.currentTime * 100) /
      this.currentTrack.player.duration;
  }

  //Function to run when player is paused by user
  public pauseListener(): void {
    this.currentTrack.player.removeEventListener(
      'timeupdate',
      this.playbackListener
    );
    // console.log('Track progress listener removed. All cleaned up!!!');
  }

  public next(index: number): void {
    // console.log('Current Index: ', this.index);
    // console.log(this.currentTrack.player.duration);
    this.index = this.risingTracks.findIndex(
      (track) => track.id === this.currentTrack.id
    );
    this.index++;
    if (this.index > this.risingTracks.length - 1) {
      this.index = 0;
    }
    // console.log('New Index: ', this.index);
    this.toggleTrack(this.risingTracks[this.index]);
  }

  public trackArtists(track: IRisingTrack): string {
    let artists = track.artists.map((art) => {
      return art.name;
    });
    // artists = artists.join(', ');
    return artists.join(', ');
  }

  public nextPage(): void {
    if (this.page + 1 <= this.numberOfPages) {
      this.page += 1;
      this.skip += this.page * this.limit;
    }
  }

  public formerPage(): void {
    if (this.page - 1 >= 1) {
      this.page -= 1;
    }
  }

  public updateItemsPerPage(totalItems: number): void {
    this.itemsPerPage = totalItems;
  }

  public async logout() {
    await dispatchUserLogOut(this.$store);
  }

  // TODO: add function to query more rising tracks when user hits bottom of scroll

  @Watch('queryParams')
  public async newRisingTracks() {
    console.log('Query Params were updated');
    this.loading = true;
    await dispatchGetRisingTracks(this.$store, { params: this.queryParams });
    this.pause();
    this.loading = false;
  }

  // TODO
  // copyLink() {
  // const markup = this.$refs.link;
  // console.log(markup);
  // console.log(document.execCommand('selectAll', false, null));
  // markup.focus();
  // document.execCommand('selectAll', false, null);
  // this.copied = document.execCommand('copy');
  // }

  public async created() {
    if (readRisingTracks(this.$store).length === 0) {
      this.loading = true;
      await dispatchGetRisingTracks(this.$store, { params: this.queryParams });
      this.loading = false;
    }
  }
}
</script>

<style scoped>
.primary-grad {
  background: linear-gradient(180.17deg, #8026a669 10.58%, #276ba665 89.42%);
  color: linear-gradient(202.17deg, #7f26a6 8.58%, #276ba6 91.42%);
}

.v-input {
  font-size: 12px;
}
</style>

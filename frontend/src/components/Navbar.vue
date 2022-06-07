<template>
  <div>
    <v-navigation-drawer clipped expand-on-hover v-model="drawer" app>
      <v-list dense nav>
        <v-list-item link to="/main/rising-tracks">
          <v-list-item-icon>
            <v-icon>web</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Rising Tracks</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item link to="/main/user-dashboard">
          <v-list-item-icon>
            <v-icon>mdi-account</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Profile</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item link to="/main/playlist">
          <v-list-item-icon>
            <v-icon>mdi-play</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Your MusicAI Mix</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-spacer></v-spacer>
        <v-list-item link @click="logout">
          <v-list-item-icon>
            <v-icon>close</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Logout</v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-divider></v-divider>

        <v-list-group v-show="adminAccess" :value="true" no-action sub-group>
          <template v-slot:activator>
            <v-list-item-content>
              <v-list-item-title>Admin</v-list-item-title>
            </v-list-item-content>
          </template>
          <v-list-item to="/main/admin/users/all" link>
            <v-list-item-icon>
              <v-icon>mdi-account-multiple-outline</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>Manage Users</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
          <v-list-item link>
            <v-list-item-icon>
              <v-icon>mdi-cog-outline</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>Settings</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list-group>
      </v-list>
      <slot name="more"></slot>
    </v-navigation-drawer>

    <!-- <slot name="app-bar"></slot> -->
    <v-app-bar color="#8026a6b2" dense dark clipped-left app>
      <v-app-bar-nav-icon
        v-if="$vuetify.breakpoint.mobile"
        @click="drawer = true"
      ></v-app-bar-nav-icon>

      <v-btn icon to="/">
        <v-icon>mdi-music</v-icon>
      </v-btn>

      <v-toolbar-title v-if="!$vuetify.breakpoint.mobile" class="mr-4">
        MusicAI
      </v-toolbar-title>

      <template v-if="$vuetify.breakpoint.mobile">
        <v-spacer></v-spacer>
      </template>

      <slot name="app-bar-extension"></slot>
    </v-app-bar>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Prop, Watch } from 'vue-property-decorator';
import {
  readDashboardMiniDrawer,
  readDashboardShowDrawer,
  readHasAdminAccess,
  readIsLoggedIn,
} from '@/store/main/getters';
import {
  commitSetDashboardShowDrawer,
  commitSetDashboardMiniDrawer,
} from '@/store/main/mutations';
import {
  dispatchCheckLoggedIn,
  dispatchCheckLoggedInSpotify,
  dispatchUserLogOut,
  dispatchGetRisingTracks,
} from '@/store/main/actions';

@Component
export default class Navbar extends Vue {
  public expandOnHover: boolean = true;
  public drawer: boolean = true;
  public adminAccess: boolean = false;
  public admins = [
    ['Manage Users', 'mdi-account-multiple-outline'],
    ['Settings', 'mdi-cog-outline'],
  ];

  //   public get miniDrawer() {
  //     return readDashboardMiniDrawer(this.$store);
  //   }

  //   public get showDrawer() {
  //     return readDashboardShowDrawer(this.$store);
  //   }

  //   public set showDrawer(value) {
  //     commitSetDashboardShowDrawer(this.$store, value);
  //   }

  public hasAdminAccess() {
    const adminAccess = readHasAdminAccess(this.$store);
    if (adminAccess) {
      this.adminAccess = adminAccess;
    } else {
      this.adminAccess = false;
    }
  }

  public async logout() {
    await dispatchUserLogOut(this.$store);
  }
}
</script>

<style scoped>
.v-input {
  font-size: 6px;
}
</style>

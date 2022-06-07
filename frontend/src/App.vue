<template>
  <v-app>
    <!-- <v-navigation-drawer app expand-on-hover clipped v-model="drawer">
      <v-list-item to="/">
        <v-list-item-content>
          <v-list-item-icon>
            <v-icon>mdi-music</v-icon>
          </v-list-item-icon>
        </v-list-item-content>
      </v-list-item>

      <v-divider></v-divider>

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

        <v-list-group v-show="hasAdminAccess" :value="true" no-action sub-group>
          <template v-slot:activator>
            <v-list-item-content>
              <v-list-item-title>Admin</v-list-item-title>
            </v-list-item-content>
          </template>
          <v-list-item to="/main/admin/users/all" link>
            <v-list-item-icon>
              <v-icon>group</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>Manage Users</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
          <v-list-item link>
            <v-list-item-icon>
              <v-icon>mdi-cog</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>Settings</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list-group>
      </v-list>
    </v-navigation-drawer> -->

    <Navbar v-if="showNav"></Navbar>
    <!-- <Navbar></Navbar> -->

    <!-- Sizes your content based upon application components -->
    <v-main>
      <!-- Provides the application the proper gutter -->
      <v-container fluid>
        <v-fade-transition mode="out-in">
          <RouterComponent></RouterComponent>
        </v-fade-transition>
        <NotificationsManager></NotificationsManager>
      </v-container>
    </v-main>

    <!-- <v-footer app> -->
    <!-- -->
    <!-- </v-footer> -->
  </v-app>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { appName } from '@/env';
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
import NotificationsManager from '@/components/NotificationsManager.vue';
import Navbar from '@/components/Navbar.vue';
import RouterComponent from '@/components/RouterComponent.vue';

import {
  dispatchCheckLoggedIn,
  dispatchCheckLoggedInSpotify,
  dispatchUserLogOut,
  dispatchGetRisingTracks,
} from '@/store/main/actions';
import { store } from '@/store';

const routeGuardMain = async (to, from, next) => {
  await dispatchCheckLoggedIn(store);
  // await dispatchCheckLoggedInSpotify(store);

  // console.log('User logged in: ', readIsLoggedIn(store));
  console.log('From route: ', from.path);
  console.log('To route: ', to.path);
  const isLoggedIn = readIsLoggedIn(store);
  // console.log('User logged in: ', isLoggedIn);
  if (isLoggedIn === true) {
    // console.log('inside isLoggedIn conditional');
    if (to.path === '/main' || to.path === '/') {
      next('/main/user-dashboard');
    } else {
      next();
    }
  } else {
    if (to.path === '/main/profile/create') {
      next();
    } else if (to.path === '/' || (to.path as string).startsWith('/main')) {
      console.log('redirecting to login');
      next('/login');
    } else {
      console.log('login');
      next();
    }
  }
};

@Component({
  components: {
    RouterComponent,
    NotificationsManager,
    Navbar,
  },
})
export default class App extends Vue {
  public appName = appName;
  public admins = [
    ['Manage Users', 'mdi-account-multiple-outline'],
    ['Settings', 'mdi-cog-outline'],
  ];
  public drawer = true;
  // public showNav = true;

  public beforeRouteEnter(to, from, next) {
    routeGuardMain(to, from, next);
  }

  public beforeRouteUpdate(to, from, next) {
    routeGuardMain(to, from, next);
  }

  public async created() {
    // await dispatchCheckLoggedIn(this.$store);
    // await dispatchCheckLoggedInSpotify(this.$store);
  }

  public get showNav() {
    // TODO: make this a store variable
    const path = this.$route.path;
    if (path && path === '/main/rising-tracks') {
      return false;
    } else {
      return true;
    }
  }

  public get loggedIn() {
    return readIsLoggedIn(this.$store);
  }

  public get miniDrawer() {
    return readDashboardMiniDrawer(this.$store);
  }

  public get showDrawer() {
    return readDashboardShowDrawer(this.$store);
  }

  public set showDrawer(value) {
    commitSetDashboardShowDrawer(this.$store, value);
  }

  public get hasAdminAccess() {
    return readHasAdminAccess(this.$store);
  }

  public switchShowDrawer() {
    commitSetDashboardShowDrawer(
      this.$store,
      !readDashboardShowDrawer(this.$store)
    );
  }

  public switchMiniDrawer() {
    commitSetDashboardMiniDrawer(
      this.$store,
      !readDashboardMiniDrawer(this.$store)
    );
  }

  public async logout() {
    await dispatchUserLogOut(this.$store);
  }
}
</script>

import Vue from 'vue';
import VueRouter from 'vue-router';
import { component } from 'vue/types/umd';

import RouterComponent from './components/RouterComponent.vue';

Vue.use(VueRouter);

export default new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      component: () => import(/* webpackChunkName: "start" */ './App.vue'),
      children: [
        {
          path: 'login',
          // route level code-splitting
          // this generates a separate chunk (about.[hash].js) for this route
          // which is lazy-loaded when the route is visited.
          component: () =>
            import(/* webpackChunkName: "login" */ './views/Login.vue'),
        },
        {
          path: 'recover-password',
          component: () =>
            import(
              /* webpackChunkName: "recover-password" */ './views/PasswordRecovery.vue'
            ),
        },
        {
          path: 'reset-password',
          component: () =>
            import(
              /* webpackChunkName: "reset-password" */ './views/ResetPassword.vue'
            ),
        },
        {
          path: 'spotify-login',
          component: () =>
            import(
              /* webpackChunkName: "spotify-login" */ './views/SpotifyLogin.vue'
            ),
        },
        {
          path: 'callback',
          component: () =>
            import(
              /* webpackChunkName: "callback" */ './views/SpotifyCallback.vue'
            ),
        },
        {
          path: 'main',
          redirect: 'main/user-dashboard',
          component: RouterComponent,
          // component: () => import(/* webpackChunkName: "main" */ './App.vue'),
          children: [
            {
              path: 'user-dashboard',
              component: () =>
                import(
                  /* webpackChunkName: "main-user-dashboard" */ './views/main/UserDashboard.vue'
                ),
            },
            {
              path: 'rising-tracks',
              // redirect: 'rising-tracks',
              component: () =>
                import(
                  /* webpackChunkName: "rising-tracks" */ './views/main/RisingTracks.vue'
                ),
            },
            {
              path: 'playlist',
              // redirect: 'rising-tracks',
              component: () =>
                import(
                  /* webpackChunkName: "playlist" */ './views/main/UserPlaylist.vue'
                ),
            },
            {
              path: 'profile',
              component: RouterComponent,
              redirect: 'profile/view',
              children: [
                {
                  path: 'view',
                  component: () =>
                    import(
                      /* webpackChunkName: "main-profile" */ './views/main/profile/UserProfile.vue'
                    ),
                },
                {
                  path: 'edit',
                  component: () =>
                    import(
                      /* webpackChunkName: "main-profile-edit" */ './views/main/profile/UserProfileEdit.vue'
                    ),
                },
                {
                  path: 'password',
                  component: () =>
                    import(
                      /* webpackChunkName: "main-profile-password" */ './views/main/profile/UserProfileEditPassword.vue'
                    ),
                },
                {
                  path: 'create',
                  component: () =>
                    import(
                      /* webpackChunkName: "main-profile-create" */ './views/main/profile/UserProfileCreate.vue'
                    ),
                },
              ],
            },
            {
              path: 'admin',
              component: () =>
                import(
                  /* webpackChunkName: "main-admin" */ './views/main/admin/Admin.vue'
                ),
              redirect: 'admin/users/all',
              children: [
                {
                  path: 'users',
                  redirect: 'users/all',
                },
                {
                  path: 'users/all',
                  component: () =>
                    import(
                      /* webpackChunkName: "main-admin-users" */ './views/main/admin/AdminUsers.vue'
                    ),
                },
                {
                  path: 'users/edit/:id',
                  name: 'main-admin-users-edit',
                  component: () =>
                    import(
                      /* webpackChunkName: "main-admin-users-edit" */ './views/main/admin/EditUser.vue'
                    ),
                },
                {
                  path: 'users/create',
                  name: 'main-admin-users-create',
                  component: () =>
                    import(
                      /* webpackChunkName: "main-admin-users-create" */ './views/main/admin/CreateUser.vue'
                    ),
                },
              ],
            },
          ],
        },
      ],
    },
    {
      path: '/*',
      redirect: '/main/user-dashboard',
    },
  ],
});

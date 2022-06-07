// import '@mdi/font/css/materialdesignicons.css'; // Ensure you are using css-loader
import Vue from 'vue';
import Vuetify from 'vuetify';

Vue.use(Vuetify);

export default new Vuetify({
  icons: {
    iconfont: 'mdi',
  },
  theme: {
    dark: true,
    themes: {
      // light: {
      //   primary: '...',
      //   ...
      // },
      dark: {
        primary: '7F26A6',
        gold: 'FFC107',
      },
    },
  },
});

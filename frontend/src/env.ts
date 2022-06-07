const env = process.env.VUE_APP_ENV;

let envApiUrl = '';
let spotRedirectURI = '';

if (env === 'production') {
  envApiUrl = `https://${process.env.VUE_APP_DOMAIN_PROD}`;
  spotRedirectURI = `${envApiUrl}/callback`;
} else if (env === 'staging') {
  envApiUrl = `https://${process.env.VUE_APP_DOMAIN_STAG}`;
  spotRedirectURI = `${envApiUrl}/callback`;
} else {
  envApiUrl = `http://${process.env.VUE_APP_DOMAIN_DEV}`;
  spotRedirectURI = `${envApiUrl}:8080/callback`;
}

export const apiUrl = envApiUrl;
export const appName = process.env.VUE_APP_NAME;
export const spotifyClientID = process.env.VUE_APP_SPOTIFY_CLIENT_ID;
export const spotifyClientSecret = process.env.VUE_APP_SPOTIFY_CLIENT_SECRET;
export const spotifyScopes =
  'ugc-image-upload user-read-recently-played user-read-playback-state user-top-read app-remote-control playlist-modify-public user-modify-playback-state playlist-modify-private user-follow-modify user-read-currently-playing user-follow-read user-library-modify user-read-playback-position playlist-read-private user-read-email user-read-private user-library-read playlist-read-collaborative';
export const spotifyRedirectURI = spotRedirectURI;

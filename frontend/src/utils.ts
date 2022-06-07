import numeral from 'numeral';
import { IRisingTrack } from './interfaces';

export const formatPlaycount = (playcount: number | string) =>
  numeral(playcount).format('0.00a');
export const formatGrowthRate = (rate: number | string) =>
  numeral(rate).format('0.00a%');
export const formatChange = (change: number | string) =>
  numeral(change).format('0.0[0]a');

export const getLocalToken = () => localStorage.getItem('token');
export const saveLocalToken = (token: string) =>
  localStorage.setItem('token', token);
export const removeLocalToken = () => localStorage.removeItem('token');

export const spotifyTokenExpired = (expires_at: number) => {
  const elapsed = expires_at - Date.now(); // in milliseconds
  const elapsedInSec = Math.floor(elapsed / 1000); // convert time to seconds
  const expiredThreshold = 60 * 2; // 2 minutes

  return elapsedInSec <= expiredThreshold;
};

export const getLocalAuthCode = () => localStorage.getItem('spotify_auth_code');
export const saveLocalAuthCode = (code: string) =>
  localStorage.setItem('spotify_auth_code', code);
export const removeLocalAuthCode = () =>
  localStorage.removeItem('spotify_auth_code');

export const getLocalSpotifyToken = () => localStorage.getItem('spotify_token');
export const saveLocalSpotifyToken = (token: string) =>
  localStorage.setItem('spotify_token', token);
export const removeLocalSpotifyToken = () =>
  localStorage.removeItem('spotify_token');

export const getLocalSpotifyRefreshToken = () =>
  localStorage.getItem('spotify_refresh_token');
export const saveLocalSpotifyRefreshToken = (token: string) =>
  localStorage.setItem('spotify_refresh_token', token);
export const removeLocalSpotifyRefreshToken = () =>
  localStorage.removeItem('spotify_refresh_token');

export const getLocalSpotifyExpiresIn = () =>
  localStorage.getItem('spotify_token_expires_in');
export const saveLocalSpotifyExpiresIn = (time: number) =>
  localStorage.setItem('spotify_token_expires_in', time.toString());
export const removeLocalSpotifyExpiresIn = () =>
  localStorage.removeItem('spotify_token_expires_in');

export const getLocalSpotifyExpiresAt = () =>
  localStorage.getItem('spotify_token_expires_at');
export const saveLocalSpotifyExpiresAt = (time: number) =>
  localStorage.setItem('spotify_token_expires_at', time.toString());
export const removeLocalSpotifyExpiresAt = () =>
  localStorage.removeItem('spotify_token_expires_at');

export const trackArtists = (track: any) => {
  let artists = track.artists.map((art) => {
    return art.name;
  });
  // artists = artists.join(', ');
  return artists.join(', ');
};

export const titleCase = (str: string) => {
  return str
    .toLowerCase()
    .split(' ')
    .map((word) => {
      return word.replace(word[0], word[0].toUpperCase());
    })
    .join(' ');
};

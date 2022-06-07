import {
  ISpotifyToken,
  IUserProfile,
  IRisingTrack,
  IUserPlaylist,
} from '@/interfaces';

export interface AppNotification {
  content: string;
  color?: string;
  showProgress?: boolean;
}

export interface MainState {
  spotifyAuthCode: string;
  spotifyToken: ISpotifyToken | null;
  isLoggedInSpotify: boolean | null;
  token: string;
  isLoggedIn: boolean | null;
  logInError: boolean;
  userProfile: IUserProfile | null;
  dashboardMiniDrawer: boolean;
  dashboardShowDrawer: boolean;
  notifications: AppNotification[];
  risingTracks: IRisingTrack[];
  currentTrack: IRisingTrack | null;
  userPlaylist: IUserPlaylist | null;
}

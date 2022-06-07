export interface ISpotifyAuthCode {
  code?: string;
  state?: string;
}

export interface ISpotifyToken {
  access_token: string;
  token_type: string;
  scope: string;
  expires_in: number;
  refresh_token?: string;
  expires_at?: number;
}

export interface IRisingTrackParams {
  lag_days: number;
  order_by: string;
  min_growth_rate: number;
  max_growth_rate: number;
  min_playcount: number;
  max_playcount: number;
  min_chg: number;
  max_chg: number;
  min_probability: number;
  max_probability: number;
  min_musicai_score: number;
  max_musicai_score: number;
  skip: number;
  limit: number;
}

export interface IUserProfile {
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  full_name: string;
  id: number;
  spotify_id?: string;
}

export interface IUserProfileUpdate {
  email?: string;
  full_name?: string;
  password?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  spotify_id?: string;
}

export interface IUserProfileCreate {
  email: string;
  full_name?: string;
  password?: string;
  is_active?: boolean;
  is_superuser?: boolean;
}

export interface ITrack {
  id: string;
  name?: string;
  track_number?: string;
  explicit?: boolean;
  duration_ms?: number;
  preview_url?: string;
  isrc?: string;
  album_id: string;
}

export interface ITrackPlay {
  track: ITrack;
  isPlaying?: boolean;
}

export interface ILabel {
  id?: string;
  name: string;
}

export interface IGenre {
  id: string;
}

export interface IAlbum {
  id: string;
  name?: string;
  release_date?: Date | string;
  total_tracks?: number;
  type?: string;
  cover?: string;
  label_id?: string;
}

export interface IArtist {
  id: string;
  name?: string;
  verified?: boolean;
  active?: boolean;
  genres?: IGenre[];
}

export interface IRisingTrackBase {
  id: string;
  playcount: string;
  chg: number;
  growth_rate: number;
  period_days: number;
  prediction?: number;
  probability?: number;
  musicai_score?: number;
  track: ITrack;
  artists: IArtist[];
  album: IAlbum;
}

export interface IRisingTrack extends IRisingTrackBase {
  name?: string;
  artists_str?: string;
  album_name?: string;
  player?: HTMLAudioElement;
  progress?: number;
}

export interface IUserPlaylist {
  user_id?: number;
  playlist_id?: string;
  playlist_url?: string;
  tracks: Array<any>;
}

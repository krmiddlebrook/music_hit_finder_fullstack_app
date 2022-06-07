from typing import Optional
import io
from pathlib import Path

import numpy as np
import librosa as lb
import requests
from requests.exceptions import ConnectionError
from pydub import AudioSegment

from app.core.config import settings
from app.spotify.parser.base import ParseBase
from app.schemas.spectrogram import Spectrogram, SpectrogramCreate


class ParseSpectrogram(ParseBase[Spectrogram, SpectrogramCreate]):
    def __init__(self, model: Spectrogram):
        super().__init__(model)

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"  # noqa
        }

    def clip_spectrogram(self, song: np.ndarray, length: int = 1765) -> np.ndarray:
        # spec needs 1765 length for the model
        clipped = np.zeros((96, length))
        if song.shape[1] < length:
            clipped[:96, : song.shape[1]] = song[:96, : song.shape[1]]
        else:
            clipped[:96, :length] = song[:96, :length]
        return clipped

    def download_wav(
        self,
        track_id: str,
        preview_url: str,
        *,
        mp3_path: Path = settings.MP3_DIR,
        wav_path: Path = settings.WAV_DIR,
        conn_timeout: int = 3,
        read_timeout: int = int(60 * 1.5),
    ) -> Optional[Path]:
        """
        Download mp3, convert it to WAV format, and store it on disk.
        """
        try:
            mp3 = None
            attempts = 0
            while not mp3 and attempts <= 3:
                r = requests.get(
                    preview_url,
                    headers=self.headers,
                    timeout=(conn_timeout, read_timeout),
                )
                # Write out to mp3 file-like object.
                mp3 = io.BytesIO(r.content)
                if mp3:
                    # Check that the mp3 downloaded correctly.
                    mp3 = AudioSegment.from_file(mp3, format="mp3")
                if mp3:
                    # Write out to wav file.
                    wav_path = wav_path / f"{track_id}.wav"
                    mp3.export(wav_path, format="wav")
                    return wav_path
                else:
                    attempts += 1
        except ConnectionError:
            print(f"Conn. Error: {track_id}")
            return None
        except Exception as err:
            print(f"Error downloading spectrogram for {track_id}, \n {err}")
            raise err

    def wav2spec(
        self,
        wav_path: Path,
        spectrogram_type: str,
        hop_size: int,
        window_size: int,
        n_mels: int,
        delete_wav: bool = True,
    ) -> Optional[SpectrogramCreate]:
        """
        Convert wav to a valid Spectrogram object.
        """
        spec = None
        if spectrogram_type != settings.SPECTROGRAM_TYPE:
            raise ValueError(
                f"{settings.SPECTROGRAM_TYPE} is the only supported spectrogram type."
            )

        try:
            # Load the wav file to a numpy array using librosa.
            y, sr = lb.load(
                str(wav_path),
                sr=settings.SAMPLE_RATE,
                offset=0,
                duration=30,
                res_type="kaiser_fast",
            )
        except Exception as e:
            print(f"Error loading wav: {wav_path}")
            raise e
        finally:
            if delete_wav:
                # Remove wav temp file.
                wav_path.unlink()

        try:
            # Convert wav to log mel-spectrogram.
            spec = lb.feature.melspectrogram(
                y, sr=sr, hop_length=hop_size, n_fft=window_size, n_mels=n_mels,
            ).astype(np.float32)
            spec = self.clip_spectrogram(np.log10(10000 * spec + 1))

            # Write spectrogram out to bytes file-like object
            output = io.BytesIO()
            np.save(output, spec)
            output.seek(0)
        except Exception as e:
            print(f"Error converting wav to spectrogram: {wav_path}")
            raise e

        # Create spectrogram object.
        spec_obj = None
        try:

            spec_obj = SpectrogramCreate(
                track_id=wav_path.stem,
                spectrogram_type=spectrogram_type,
                hop_size=hop_size,
                window_size=window_size,
                n_mels=n_mels,
                is_corrupt=False,
                spectrogram=output.read(),
            )
        except Exception as e:
            spec_obj = SpectrogramCreate(
                track_id=wav_path.stem,
                spectrogram_type=spectrogram_type,
                hop_size=hop_size,
                window_size=window_size,
                n_mels=n_mels,
                is_corrupt=True,
                spectrogram=output.read(),
            )
            print(f"Error reading spectrogram: {wav_path}")
            print(e)
        finally:
            return spec_obj

    def spec2numpy(self, track_id: str, spectrogram: bytes) -> Optional[np.ndarray]:
        try:
            return np.load(io.BytesIO(spectrogram))
        except Exception as corrupt_spec:
            print(f"Corrupted spectrogram: {track_id} \n {corrupt_spec}")
            return None


spectrogram = ParseSpectrogram(Spectrogram)

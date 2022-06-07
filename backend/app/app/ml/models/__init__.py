# from .HitPredictionModelv1 import HitPredictionModelv1  # noqa
# from .HitPredictionModelv2 import HitPredictionModelv2  # noqa
# from .HitPredictionModelv3 import HitPredictionModelv3  # noqa
from .CNNSpectrogram import CNNSpectrogram  # noqa
from .CNNSpectrogramV2 import CNN_SpectrogramV2  # noqa

MODEL_DICT = {
    "CNNSpectrogram": CNNSpectrogram,
    "CNNSpectrogramV2": CNN_SpectrogramV2,
}

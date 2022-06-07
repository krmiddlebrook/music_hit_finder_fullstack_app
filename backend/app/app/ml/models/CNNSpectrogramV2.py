from typing import Dict

import torch
from app.ml import torch_utils


class CNN_SpectrogramV2(torch.nn.Module):
    """
    Basically CNN_Spectrogram except with leaky_relu, avg pooling, and batchnorm.
    """

    def __init__(self, output_dims=2, dropout=False):
        super(CNN_SpectrogramV2, self).__init__()
        self.name = "CNNSpectrogramV2"
        self.output_dims = output_dims
        self.use_dropout = dropout
        # (B x 96 x 1765)
        dim = 1765
        self.input_shape = (96, 1765)
        self.conv2 = torch_utils.conv1d(
            in_channels=96,
            out_channels=256,
            kernel_size=3,
            stride=1,
            padding=torch_utils.get_padding(dim, 3, 1, dim),
            leaky_relu=True,
            batch_norm=True,
        )  # (B x 256 x 1765)
        self.avg2 = torch.nn.AvgPool1d(
            kernel_size=3, stride=3, padding=torch_utils.get_padding(dim, 3, 1, dim)
        )  # (B x 256 x 589)
        dim = (dim // 3) + 1
        self.conv3 = torch_utils.conv1d(
            in_channels=256,
            out_channels=256,
            kernel_size=3,
            stride=1,
            padding=torch_utils.get_padding(dim, 3, 1, dim),
            leaky_relu=True,
            batch_norm=True,
        )  # (B x 256 x 589)
        self.avg3 = torch.nn.AvgPool1d(
            kernel_size=3, stride=3, padding=torch_utils.get_padding(dim, 3, 1, dim)
        )  # (B x 256 x 197)
        dim = (dim // 3) + 1
        self.conv4 = torch_utils.conv1d(
            in_channels=256,
            out_channels=256,
            kernel_size=3,
            stride=1,
            padding=torch_utils.get_padding(dim, 3, 1, dim),
            leaky_relu=True,
            batch_norm=True,
        )  # (B x 128 x 197)
        self.avg4 = torch.nn.AvgPool1d(
            kernel_size=3, stride=3, padding=torch_utils.get_padding(dim, 3, 1, dim)
        )  # (B x 128 x 66)
        dim = (dim // 3) + 1
        self.conv5 = torch_utils.conv1d(
            in_channels=256,
            out_channels=128,
            kernel_size=3,
            stride=1,
            padding=torch_utils.get_padding(dim, 3, 1, dim),
            leaky_relu=True,
            batch_norm=True,
        )  # (B x 64 x 66)
        self.avg5 = torch.nn.AvgPool1d(
            kernel_size=3, stride=3, padding=torch_utils.get_padding(dim, 3, 1, dim)
        )  # (B x 64 x 23)
        dim = (dim // 3) + 1
        self.conv6 = torch_utils.conv1d(
            in_channels=128,
            out_channels=64,
            kernel_size=3,
            stride=1,
            padding=torch_utils.get_padding(dim, 3, 1, dim),
            leaky_relu=True,
            batch_norm=True,
        )  # (B x 32 x 23)
        self.avg6 = torch.nn.AvgPool1d(
            kernel_size=3, stride=3, padding=torch_utils.get_padding(dim, 3, 1, dim)
        )  # (B x 32 x 8)
        self.conv7 = torch_utils.conv1d(
            in_channels=64,
            out_channels=16,
            kernel_size=3,
            stride=1,
            padding=torch_utils.get_padding(dim, 3, 1, dim),
            relu=False,
        )  # (B x 16 x 8)
        self.dropout = torch.nn.Dropout(0.5)
        self.linear = torch.nn.Linear(
            in_features=128, out_features=output_dims, bias=True
        )

    def get_dict(self, x) -> Dict[str, torch.Tensor]:
        out = {}
        # out["conv1"] = self.conv1(x)
        # out["avg1"] = self.avg1(out["conv1"])
        out["conv2"] = self.conv2(x)
        out["avg2"] = self.avg2(out["conv2"])
        out["conv3"] = self.conv3(out["avg2"])
        out["avg3"] = self.avg3(out["conv3"])
        out["conv4"] = self.conv4(out["avg3"])
        out["avg4"] = self.avg4(out["conv4"])
        out["conv5"] = self.conv5(out["avg4"])
        out["avg5"] = self.avg5(out["conv5"])
        out["conv6"] = self.conv6(out["avg5"])
        out["avg6"] = self.avg6(out["conv6"])
        out["conv7"] = self.conv7(out["avg6"])
        if self.use_dropout:
            out["dropout"] = self.dropout(out["conv7"])
            out["flatten"] = out["dropout"].view(out["dropout"].size(0), -1)
        else:
            out["flatten"] = out["conv7"].view(out["conv7"].size(0), -1)
        out["linear"] = self.linear(out["flatten"])
        return out

    def forward(self, x) -> torch.Tensor:
        out = self.get_dict(x)
        # out["sigmoid"] = torch.nn.Sigmoid()(out["linear"])
        return out["linear"]

    def output_features(self, x) -> torch.Tensor:
        out = self.get_dict(x)
        # out["sigmoid"] = torch.nn.Sigmoid()(out["linear"])
        return out["flatten"]

    def output_probabilities(self, x) -> torch.Tensor:
        linear = self.forward(x)
        return torch.nn.Sigmoid()(linear)

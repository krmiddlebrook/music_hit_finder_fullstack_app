import torch
from app.ml import torch_utils


class CNNSpectrogram(torch.nn.Module):
    def __init__(self, output_dims=2):
        super(CNNSpectrogram, self).__init__()
        self.name = "CNNSpectrogram"
        self.output_dims = output_dims
        # (B x 96 x 1765)
        dim = 1765
        self.input_shape = (96, 1765)
        self.conv2 = torch_utils.conv1d(
            in_channels=96,
            out_channels=256,
            kernel_size=3,
            stride=1,
            padding=torch_utils.get_padding(dim, 3, 1, dim),
            relu=True,
        )  # (B x 256 x 1765)
        self.max2 = torch.nn.MaxPool1d(
            kernel_size=3, stride=3, padding=torch_utils.get_padding(dim, 3, 1, dim)
        )  # (B x 256 x 589)
        dim = (dim // 3) + 1
        self.conv3 = torch_utils.conv1d(
            in_channels=256,
            out_channels=256,
            kernel_size=3,
            stride=1,
            padding=torch_utils.get_padding(dim, 3, 1, dim),
            relu=True,
        )  # (B x 256 x 589)
        self.max3 = torch.nn.MaxPool1d(
            kernel_size=3, stride=3, padding=torch_utils.get_padding(dim, 3, 1, dim)
        )  # (B x 256 x 197)
        dim = (dim // 3) + 1
        self.conv4 = torch_utils.conv1d(
            in_channels=256,
            out_channels=256,
            kernel_size=3,
            stride=1,
            padding=torch_utils.get_padding(dim, 3, 1, dim),
            relu=True,
        )  # (B x 128 x 197)
        self.max4 = torch.nn.MaxPool1d(
            kernel_size=3, stride=3, padding=torch_utils.get_padding(dim, 3, 1, dim)
        )  # (B x 128 x 66)
        dim = (dim // 3) + 1
        self.conv5 = torch_utils.conv1d(
            in_channels=256,
            out_channels=128,
            kernel_size=3,
            stride=1,
            padding=torch_utils.get_padding(dim, 3, 1, dim),
            relu=True,
        )  # (B x 64 x 66)
        self.max5 = torch.nn.MaxPool1d(
            kernel_size=3, stride=3, padding=torch_utils.get_padding(dim, 3, 1, dim)
        )  # (B x 64 x 23)
        dim = (dim // 3) + 1
        self.conv6 = torch_utils.conv1d(
            in_channels=128,
            out_channels=64,
            kernel_size=3,
            stride=1,
            padding=torch_utils.get_padding(dim, 3, 1, dim),
            relu=True,
        )  # (B x 32 x 23)
        self.max6 = torch.nn.MaxPool1d(
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

    def get_dict(self, x):
        out = {}
        # out["conv1"] = self.conv1(x)
        # out["max1"] = self.max1(out["conv1"])
        out["conv2"] = self.conv2(x)
        out["max2"] = self.max2(out["conv2"])
        out["conv3"] = self.conv3(out["max2"])
        out["max3"] = self.max3(out["conv3"])
        out["conv4"] = self.conv4(out["max3"])
        out["max4"] = self.max4(out["conv4"])
        out["conv5"] = self.conv5(out["max4"])
        out["max5"] = self.max5(out["conv5"])
        out["conv6"] = self.conv6(out["max5"])
        out["max6"] = self.max6(out["conv6"])
        out["conv7"] = self.conv7(out["max6"])
        out["dropout"] = self.dropout(out["conv7"])
        out["flatten"] = out["conv7"].view(out["dropout"].size(0), -1)
        out["linear"] = self.linear(out["flatten"])
        return out

    def forward(self, x):
        out = self.get_dict(x)
        # out["sigmoid"] = torch.nn.Sigmoid()(out["linear"])
        return out["linear"]

    def output_features(self, x):
        out = self.get_dict(x)
        out["sigmoid"] = torch.nn.Sigmoid()(out["linear"])
        return out

    def output_probabilities(self, x):
        linear = self.forward(x)
        return torch.nn.Sigmoid()(linear)

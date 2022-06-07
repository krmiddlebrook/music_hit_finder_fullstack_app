import numpy as np

import torch


# convolutional
def outputSize(in_size, kernel_size, stride, padding=0):
    output = int((in_size - kernel_size + 2 * (padding)) / stride) + 1

    return output


def linear(
    in_features,
    out_features,
    batch_norm=False,
    init_zero_weights=False,
    xavier_init=False,
    kaiming=False,
    relu=True,
    leaky_relu=False,
    bias=True,
):
    """
        Creates a convolutional layer, with optional batch normalization.
    """
    layers = []
    linear_layer = torch.nn.Linear(
        in_features=in_features, out_features=out_features, bias=bias,
    )

    if init_zero_weights:
        linear_layer.weight.data = torch.randn(in_features, out_features) * 0.001

    if xavier_init:
        linear_layer.weight.data = torch.nn.init.xavier_uniform_(
            linear_layer.weight.data
        )

    if kaiming:
        # from here, this works well with leaky relu, much better than xavier would https://arxiv.org/abs/1502.01852
        linear_layer.weight.data = torch.nn.init.kaiming_uniform_(
            linear_layer.weight.data
        )

    layers.append(linear_layer)

    if batch_norm:
        layers.append(torch.nn.BatchNorm1d(out_features))

    if relu:
        layers.append(torch.nn.ReLU())

    elif leaky_relu:
        layers.append(
            torch.nn.LeakyReLU(1.0 / 5.5)
        )  # 1.0 / 5.5 comes from https://arxiv.org/pdf/1505.00853.pdf on leaky relu for cnns

    return torch.nn.Sequential(*layers)


def conv1d(
    in_channels,
    out_channels,
    kernel_size,
    stride=1,
    padding=1,
    batch_norm=False,
    init_zero_weights=False,
    xavier_init=False,
    kaiming=False,
    w_max=False,
    relu=True,
    leaky_relu=False,
    bias=True,
):
    """
        Creates a convolutional layer, with optional batch normalization.
    """
    layers = []
    conv_layer = torch.nn.Conv1d(
        in_channels=in_channels,
        out_channels=out_channels,
        kernel_size=kernel_size,
        stride=stride,
        padding=padding,
        bias=bias,
    )
    if init_zero_weights:
        conv_layer.weight.data = (
            torch.randn(out_channels, in_channels, kernel_size, kernel_size) * 0.001
        )
    if xavier_init:
        conv_layer.weight.data = torch.nn.init.xavier_uniform_(conv_layer.weight.data)
    if kaiming:
        # from here, this works well with leaky relu, much better than xavier would https://arxiv.org/abs/1502.01852
        conv_layer.weight.data = torch.nn.init.kaiming_uniform_(conv_layer.weight.data)

    layers.append(conv_layer)
    if batch_norm:
        layers.append(torch.nn.BatchNorm1d(out_channels))

    if relu:
        layers.append(torch.nn.ReLU())

    elif leaky_relu:
        layers.append(
            torch.nn.LeakyReLU(1.0 / 5.5)
        )  # 1.0 / 5.5 comes from https://arxiv.org/pdf/1505.00853.pdf on leaky relu for cnns

    if w_max:
        layers.append(torch.nn.MaxPool1d(kernel_size=kernel_size, stride=stride))

    return torch.nn.Sequential(*layers)


def get_padding(in_size, kernel_size, stride, output_size):
    padding = (stride * (output_size - 1) + kernel_size - in_size) // 2
    return padding


def get_padding_deconv(in_size, kernel_size, stride, output_size):
    padding = int((stride * (in_size - 1) + kernel_size - output_size) / 2)
    return np.max((padding, 0))


# layers
class ResnetBlock(torch.nn.Module):
    def __init__(self, conv_dim):
        super(ResnetBlock, self).__init__()
        self.conv1 = conv1d(
            in_channels=conv_dim,
            out_channels=conv_dim,
            kernel_size=3,
            stride=1,
            padding=1,
        )
        self.conv2 = conv1d(
            in_channels=conv_dim,
            out_channels=conv_dim,
            kernel_size=3,
            stride=1,
            padding=1,
        )

    def forward(self, x):
        newx = torch.nn.ReLU()(self.conv1(x))
        newx = self.conv2(x)
        out = x + newx
        return out


class Concat(torch.nn.Module):
    def __init__(self):
        super(Concat, self).__init__()

    def forward(self, x1, x2):
        return torch.cat((x1, x2), 1)


class MusicAILSTM(torch.nn.Module):
    def __init__(self, n_features, seq_length, n_hidden, n_layers, bidirectional=True):
        super(MusicAILSTM, self).__init__()
        self.n_features = n_features
        self.seq_len = seq_length
        self.n_hidden = n_hidden
        self.n_layers = n_layers
        self.bidirectional = bidirectional
        self.lstm_layer = torch.nn.LSTM(
            input_size=n_features,
            hidden_size=self.n_hidden,
            num_layers=self.n_layers,
            batch_first=True,
            bidirectional=self.bidirectional,
        )
        # (batch_size,seq_len, self.n_hidden*self.seq_len)

    def init_hidden(self, batch_size):
        # even with batch_first = True this remains same as docs
        cuda = torch.cuda.is_available()
        device = torch.device("cuda" if cuda else "cpu")
        n_layers = self.n_layers
        if self.bidirectional:
            n_layers = self.n_layers * 2
        hidden_state = torch.zeros(n_layers, batch_size, self.n_hidden).to(device)
        cell_state = torch.zeros(n_layers, batch_size, self.n_hidden).to(device)
        self.hidden = (hidden_state, cell_state)

    def calculate(self, x, flatten=True, init_hidden=True):
        batch_size, seq_len, _ = x.size()
        if self.init_hidden:
            self.init_hidden(batch_size)
        lstm_out, self.hidden = self.lstm_layer(x, self.hidden)
        # (batch_size,seq_len,num_directions * hidden_size)
        if flatten:
            # for following linear layer we want to keep batch_size dimension and merge rest
            # .contiguous() -> solves tensor compatibility error
            lstm_out = lstm_out.contiguous().view(batch_size, -1)
        return lstm_out

    def forward(self, x, flatten=True, init_hidden=True):
        lstm_out = self.calculate(x, flatten=flatten, init_hidden=init_hidden)
        return lstm_out

    def output_hidden(self, x, flatten=True, init_hidden=True):
        lstm_out = self.calculate(x, flatten=flatten, init_hidden=init_hidden)
        return lstm_out, self.hidden


def create_linear_torch(input_dims, output_dims, relu=True, batch_norm=False):
    layers = []
    lin = torch.nn.Linear(input_dims, output_dims)
    layers.append(lin)
    if batch_norm:
        layers.append(torch.nn.BatchNorm1d(output_dims))
    if relu:
        layers.append(torch.nn.ReLU())
    return torch.nn.Sequential(*layers)

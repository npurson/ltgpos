import argparse
import socket
import sys

import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.nn.functional as F

from PIL import Image
from scipy.interpolate import interp1d
from pyts.image import GramianAngularField


DEBUG = True


class ConvFrontend(nn.Module):

    def __init__(self):
        super(ConvFrontend, self).__init__()
        self.conv = nn.Conv3d(3, 64, (3, 7, 7), stride=(1, 2, 2), padding=(2, 3, 3))
        self.norm = nn.BatchNorm3d(64)
        self.pool = nn.MaxPool3d((1, 3, 3), stride=(1, 2, 2), padding=(0, 1, 1))

    def forward(self, x):
        output = self.pool(F.relu(self.norm(self.conv(x))))
        return output


class ConvBackend(nn.Module):

    def __init__(self):
        super(ConvBackend, self).__init__()
        self.conv1 = nn.Conv1d(512, 1024, 2, 2)
        self.norm1 = nn.BatchNorm1d(1024)
        self.pool1 = nn.MaxPool1d(2, 2)
        self.linear = nn.Linear(1024, 512)
        self.norm3 = nn.BatchNorm1d(512)
        self.linear2 = nn.Linear(512, 2)

    def forward(self, x):
        x = self.conv1(x.transpose(1, 2))
        x = self.pool1(F.relu(self.norm1(x))).mean(2)
        x = self.linear2(F.relu(self.norm3(self.linear(x))))
        return x.softmax(-1)


class BasicBlock(nn.Module):

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(BasicBlock, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1   = nn.BatchNorm2d(planes)
        self.relu  = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, padding=1, bias=False)
        self.bn2   = nn.BatchNorm2d(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        identity = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        if self.downsample is not None:
            identity = self.downsample(x)

        out += identity
        out = self.relu(out)
        return out


class ResNet(nn.Module):

    def __init__(self, block, layers, num_classes=512):
        super(ResNet, self).__init__()
        self.inplanes = 64
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=2)
        self.avgpool = nn.AvgPool2d(4, stride=1)
        self.fc = nn.Linear(512, num_classes)
        self.bn2 = nn.BatchNorm1d(num_classes)

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes:
            downsample = nn.Sequential(
                nn.Conv2d(self.inplanes, planes, kernel_size=1,
                          stride=stride, bias=False),
                nn.BatchNorm2d(planes),
            )

        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes
        for _ in range(1, blocks):
            layers.append(block(self.inplanes, planes))

        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = x.flatten(1)
        x = self.fc(x)
        x = self.bn2(x)
        return x


class ResNetBBC(nn.Module):

    def __init__(self):
        super(ResNetBBC, self).__init__()
        self.resnetModel = ResNet(BasicBlock, [3, 4, 6, 3])

    def forward(self, x):
        x = x.transpose(1, 2).squeeze()
        output = self.resnetModel(x)
        return output.unsqueeze(0)


class SLDNet(nn.Module):
    def __init__(self):
        super(SLDNet, self).__init__()
        self.frontend = ConvFrontend()
        self.resnet   = ResNetBBC()
        self.backend  = ConvBackend()

    def forward(self, x):
        return self.backend(self.resnet(self.frontend(x)))


def transform(freq: int, input: np.ndarray):

    # interpolate
    f = interp1d(list(range(len(input))), input, kind='cubic')
    x = np.linspace(0, len(input) - 1, num=2000000 * len(input) // int(freq))
    input = f(x)

    input = input[:2400]
    if len(input) < 2400:
        input = np.concatenate([input, np.zeros((2400 - len(input)))])

    # sliding window
    wins = []
    for i in range(len(input) // 224):
        w = input[i * 224 : i * 224 + 448]
        if len(w) != 448:
            continue
        wins.append(w)
    gaf = GramianAngularField(image_size=112, method='summation')
    wins = gaf.fit_transform(wins)
    plt.figure(figsize=(8, 8))
    plt.axis('off')

    imgs = []
    for w in wins:
        img = plt.imshow(w)
        img = img.make_image(renderer=None)[0]
        imgs.append(Image.fromarray(img[::-1, :, :3]))
        plt.close('all')

    # image transform
    vlm = np.zeros((3, len(imgs), 112, 112), dtype=np.float32)
    for i, im in enumerate(imgs):
        im = im.resize((112, 112), Image.BILINEAR)
        im = np.asanyarray(im) / 255
        im = np.transpose(im, (2, 0, 1))
        vlm[:, i] = im
    return torch.from_numpy(vlm).unsqueeze(0)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int)
    parser.add_argument('--model')
    return parser.parse_args()


class Ltgwave(object):

    def __init__(self, port, model_path):
        self.model = SLDNet()
        self.model.load_state_dict(torch.load(model_path))
        self.model.eval()
        if DEBUG:
            print('Model loaded.')

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('localhost', port))
        self.sock.listen()
        self.listenloop()

    def listenloop(self):
        while True:
            conn, _ = self.sock.accept()
            if DEBUG:
                print('Connected')
            while True:
                byteData = conn.recv(4 * 1024 ** 2 * 8)
                if len(byteData) == 0:
                    if DEBUG:
                        print('Closed')
                        conn.close()
                    break

                while len(byteData) != (4e6 + 2) * 8:
                    byteData += conn.recv(4 * 1024 ** 2 * 8)
                data = np.frombuffer(byteData)
                flag = int(data[0])

                if flag == 0:
                    flag, freq, input = data[0], data[1], data[2:]
                    if DEBUG:
                        print('flag ', flag)
                        print('freq ', freq)
                        print('insz ', len(input))
                        print('data ', input)

                    input = transform(freq, input)
                    with torch.no_grad():
                        output = torch.argmax(self.model(input)).item()
                    if DEBUG:
                        print(' ret ', output, '\n')
                        # print('send ', conn.send(str(output).encode()))
                    conn.send(str(output).encode())

                elif flag == 1:
                    if DEBUG:
                        print('Closed')
                    conn.close()
                    break
                elif flag == 2:
                    if DEBUG:
                        print('Exited')
                    sys.exit()


if __name__ == '__main__':

    args = parse_args()
    ltgwave = Ltgwave(args.port, args.model)

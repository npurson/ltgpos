import argparse
import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d


MAX_GRD_SIZE = 1024
HEADER = 'Header'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no', type=str)
    args = parser.parse_args()
    return args


def plot_grdres(grdres, labelfile):
    """Plot gooness maps of grid research from output file.

    Args:
        grdres: path to drawdata(.txt)
        label: path to label.csv

    Structure of grdres:
        Header
        List[float] (length: MAX_GRD_SIZE ** 2 + 4 + 2)
        List[float] (length: MAX_GRD_SIZE ** 2 + 4 + 2)
        ...
        Header
        List[float] (length: MAX_GRD_SIZE ** 2 + 4 + 2)
        ...
    """
    def plot(no: int):
        # plt.savefig('figures/grdresmap_' + str(no) + '.png')
        plt.show()

    def map_pt(pt: list, bbox: list) -> list:
        return [int(MAX_GRD_SIZE * (pt[i] - bbox[2 * i]) /
                    (bbox[2 * i + 1] - bbox[2 * i]))
                for i in range(len(pt))]

    with open(grdres) as f_grdres, open(labelfile) as f_label:
        labels = iter(f_label.readlines())
        for i, line in enumerate(f_grdres.readlines()):
            line = line.strip()
            if line == HEADER:
                label = list(map(float, next(labels).split(',')[:2]))
                print('New Batch')
            else:
                blobs = list(map(float, line.split(' ')))
                grdres = np.array(blobs[:-6]).reshape((MAX_GRD_SIZE, MAX_GRD_SIZE))
                schdom = blobs[-6:-2]
                pred = map_pt(blobs[-2:], schdom)
                lbl = map_pt(label, schdom)

                xx, yy = np.meshgrid(np.arange(0, MAX_GRD_SIZE),
                                    np.arange(0, MAX_GRD_SIZE))
                fig = plt.figure()
                ax = plt.axes(projection='3d')
                ax.contour3D(xx, yy, grdres, 40)
                ax.scatter3D(pred[0], pred[1], grdres[pred[1]][pred[0]], cmap='red')
                ax.scatter3D(lbl[0], lbl[1], 0, cmap='green')
                plt.title(f'pred: {pred[0]}, {pred[1]}\n\
                            goodness: {grdres[pred[1]][pred[0]]}\n\
                            label: {lbl[0]}, {lbl[1]}', fontsize=12)
                plot(i)


if __name__ == '__main__':
    args = parse_args()
    plot_grdres('figures/grdres.txt', 'test/data/label_' + args.no + '.csv')

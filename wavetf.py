import numpy as np
import matplotlib.pyplot as plt

from PIL import Image
from scipy.interpolate import interp1d
from pyts.image import GramianAngularField


def wavetf(freq: int, input: tuple, tf):

    # interpolate
    x = list(range(len(input)))
    f = interp1d(x, list(input), kind='cubic')
    x = np.linspace(0, x[-1], num=2000000 // freq * len(input))
    input = f(x)

    input = input[:2400]
    if len(input) < 2400:
        input += [0 for _ in range(2400-len(input))]

    # sliding window
    wins = []
    for i in range(len(input) // 224):
        w = input[i * 224 : i * 224 + 448]
        if len(w) != 448:
            continue
        wins.append(w)
    wins = tf.fit_transform(wins)
    plt.figure(figsize=(8, 8))
    plt.axis('off')

    imgs = []
    for w in wins:
        img = plt.imshow(w)
        img = img.make_image(renderer=None)[0]
        imgs.append(Image.fromarray(img[::-1, :, :3]))
        plt.close('all')

    # image transform
    vlm = np.zeros((3, len(imgs), 112, 112))
    for i, im in enumerate(imgs):
        im = im.resize((112, 112), Image.BILINEAR)
        im = np.asanyarray(im) / 255
        im = np.transpose(im, (2, 0, 1))
        vlm[:, i] = im
    return vlm.flatten().tolist()  # [3, 9, 112, 112]


def build_tf():
    tf = GramianAngularField(image_size=112, method='summation')
    return tf


# def test():
#     freq = 2000000
#     input = (-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,0,0,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,0,0,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,0,0,0,0,-14,-14,-14,-14,-14,-14,-14,-14,-14,-14,0,0,0,0,-14,-14,-14,-14,0,0,0,0,0,0,-14,-14,-14,-14,-14,-14,0,0,0,0,0,-14,-14,-14,-14,-14,-14,-14,-14,0,0,-14,-14,-14,-14,-14,-14,-14,-28,-294,-630,-1050,-1400,-1638,-1778,-1862,-1974,-2100,-2240,-2394,-2562,-2716,-2842,-2954,-3024,-3066,-3094,-3094,-3066,-3024,-2982,-2926,-2856,-2786,-2716,-2646,-2576,-2506,-2422,-2366,-2282,-2226,-2156,-2072,-2016,-1946,-1876,-1820,-1750,-1680,-1624,-1568,-1512,-1456,-1400,-1358,-1302,-1260,-1218,-1176,-1120,-1078,-1036,-994,-938,-896,-854,-812,-784,-756,-728,-700,-686,-672,-644,-630,-616,-588,-574,-560,-546,-532,-518,-490,-476,-462,-448,-434,-420,-420,-406,-392,-364,-364,-350,-336,-322,-308,-294,-280,-266,-266,-252,-238,-224,-210,-210,-196,-182,-168,-154,-140,-126,-112,-98,-98,-196,-308,-420,-420,-406,-406,-448,-574,-756,-966,-1176,-1372,-1540,-1680,-1778,-1862,-1932,-2002,-2072,-2128,-2184,-2226,-2254,-2268,-2268,-2268,-2254,-2212,-2156,-2100,-2030,-1960,-1890,-1820,-1736,-1666,-1596,-1526,-1470,-1400,-1330,-1274,-1204,-1148,-1092,-1036,-980,-924,-868,-812,-756,-700,-644,-602,-546,-490,-448,-406,-378,-336,-308,-280,-266,-238,-224,-196,-182,-168,-154,-140,-140,-140,-126,-126,-126,-126,-112,-112,-112,-112,-112,-112,-98,-98,-84,-84,-70,-70,-70,-56,-56,-42,-42,-28,-28,-14,-14,0,0,14,14,28,28,42,42,56,56,14,-14,0,0,42,42,28,-70,-182,-266,-322,-378,-420,-462,-518,-602,-700,-826,-966,-1078,-1176,-1260,-1344,-1386,-1442,-1470,-1484,-1498,-1498,-1498,-1498,-1484,-1470,-1442,-1414,-1372,-1330,-1260,-1204,-1148,-1092,-1036,-966,-924,-868,-798,-756,-700,-644,-588,-546,-490,-434,-378,-336,-294,-252,-210,-168,-126,-84,-42,0,28,56,70,98,112,126,140,140,140,140,140,140,140,140,126,126,126,112,98,98,98,84,84,70,70,70,56,56,56,70,70,70,70,70,84,84,84,98,98,98,98,98,112,112,84,84,84,126,154,154,112,56,14,14,14,28,28,0,-42,-112,-182,-252,-308,-364,-406,-462,-504,-560,-630,-686,-756,-812,-882,-924,-966,-994,-1008,-1022,-1022,-1008,-994,-966,-938,-924,-896,-868,-826,-798,-756,-714,-672,-630,-588,-560,-518,-490,-462,-448,-420,-392,-364,-336,-294,-266,-224,-182,-126,-84,-42,0,28,56,84,112,126,140,154,154,154,154,154,140,140,140,126,126,112,98,84,56,42,28,14,0,-14,-28,-42,-42,-56,-70,-70,-70,-70,-70,-70,-56,-56,-42,-42,-28,-14,-14,0,14,42,42,42,28,0,14,14,28,28,28,14,-14,-56,-84,-98,-98,-112,-126,-140,-182,-224,-266,-308,-364,-392,-434,-476,-504,-532,-574,-602,-630,-644,-672,-686,-700,-714,-714,-700,-686,-672,-644,-630,-602,-588,-574,-560,-560,-546,-546,-532,-532,-518,-504,-490,-462,-448,-420,-392,-364,-336,-322,-280,-252,-224,-196,-154,-126,-98,-70,-42,-14,14,28,42,56,56,56,56,56,42,28,0,-14,-28,-42,-70,-84,-112,-126,-140,-168,-182,-196,-210,-224,-224,-224,-224,-224,-224,-210,-196,-168,-168,-154,-126,-112,-84,-84,-98,-98,-84,-42,-28,-28,-28,-42,-56,-56,-56,-42,-42,-42,-42,-70,-84,-112,-126,-140,-154,-168,-182,-196,-224,-252,-280,-308,-336,-350,-378,-392,-406,-420,-434,-434,-448,-448,-448,-448,-448,-448,-434,-434,-420,-406,-406,-406,-392,-392,-392,-392,-392,-406,-406,-406,-406,-406,-392,-392,-364,-350,-322,-308,-280,-252,-224,-196,-168,-140,-112,-84,-56,-42,-14,14,28,42,42,56,56,56,42,42,14,0,-14,-42,-56,-84,-112,-126,-140,-154,-168,-182,-182,-196,-196,-196,-196,-196,-182,-168,-154,-154,-140,-140,-126,-98,-70,-42,-28,-28,-28,-14,0,14,28,42,42,28,28,14,0,0,0,0,0,-14,-28,-56,-56,-84,-98,-112,-126,-140,-140,-154,-168,-182,-196,-210,-224,-224,-238,-252,-252,-252,-252,-252,-252,-238,-238,-238,-238,-238,-238,-238,-238,-238,-238,-238,-238,-238,-224,-224,-224,-224,-224,-224,-224,-210,-196,-182,-154,-140,-112,-84,-70,-42,-28,0,14,28,42,42,56,56,42,42,42,28,14,14,0,-14,-28,-42,-56,-84,-98,-112,-126,-140,-154,-154,-168,-168,-182,-182,-182,-196,-196,-196,-182,-168,-168,-168,-168,-154,-140,-112,-84,-70,-56,-42,-28,-28,-14,-14,0,0,0,0,0,-14,-28,-28,-42,-42,-42,-56,-70,-70,-84,-98,-98,-112,-112,-126,-126,-140,-140,-154,-168,-168,-168,-182,-182,-196,-196,-182,-182,-182,-182,-182,-182,-182,-182,-182,-182,-182,-182,-182,-182,-196,-196,-210,-210,-210,-224,-224,-224,-224,-224,-224,-224,-210,-210,-196,-196,-182,-168,-168,-154,-140,-126,-126,-126,-112,-112,-112,-112,-112,-112,-126,-126,-140,-140,-140,-154,-154,-154,-168,-168,-168,-168,-182,-182,-196,-196,-182,-182,-182,-182,-182,-182,-154,-140,-140,-126,-112,-98,-84,-70,-56,-42,-14,0,0,0,14,14,14,14,14,14,14,14,0,0,0,0,0,-14,-14,-14,-28,-42,-42,-56,-56,-70,-70,-84,-84,-98,-112,-112,-126,-126,-140,-140,-140,-140,-154,-154,-154,-154,-154,-154,-154,-154,-154,-154,-154,-168,-168,-168,-182,-182,-182,-196,-196,-196,-196,-196,-196,-196,-196,-196,-196,-196,-196,-182,-182,-182,-182,-168,-168,-168,-168,-154,-154,-154,-154,-154,-154,-154,-154,-154,-154,-154,-140,-140,-140,-126,-126,-112,-112,-112,-112,-112,-98,-98,-98,-84,-84,-84,-70,-70,-56,-42,-28,-14,-14,0,0,14,14,28,42,42,56,56,56,56,56,56,56,56,56,56,56,42,42,42,42,42,42,42,42,42,42,42,42,42,28,28,14,14,0,0,-14,-14,-28,-28,-28,-42,-42,-56,-56,-56,-70,-70,-70,-70,-70,-70,-70,-70,-70,-84,-84,-84,-84,-98,-98,-98,-112,-112,-112,-126,-126,-126,-140,-140,-140,-154,-154,-154,-154,-154,-154,-154,-154,-154,-154,-154,-154,-140,-140,-140,-126,-126,-112,-112,-98,-98,-84,-84,-70,-70,-56,-56,-56,-56,-56,-56,-56,-56,-56,-56,-56,-56,-42,-42,-28,-28,-28,-14,-14,0,0,14,28,28,42,56,56,70,84,84,98,98,112,112,126,126,126,126,140,140,154,154,154,154,154,154,154,154,140,140,126,126,112,98,84,84,70,56,56,42,42,28,28,28,28,28,28,28,28,28,28,28,28,28,28,28,28,28,14,14,14,0,0,-14,-14,-14,-28,-28,-28,-28,-28,-28,-28,-28,-28,-28,-28,-28,-14,-14,-14,-14,0,0,0,14,14,14,14,14,14,14,14,14,0,0,0,-14,-14,-14,-14,-14,0,0,0,14,14,28,42,56,84,98,112,126,154,168,182,196,210,238,252,266,266,280,294,308,322,322,336,336,350,350,364,364,378,378,378,378,378,364,364,364,350,336,322,308,294,280,266,252,238,224,210,210,196,196,196,196,182,182,182,182,182,182,182,182,168,168,168,168,154,154,154,140,126,126,126,112,112,112,112,98,98,98,98,98,98,98,98,98,98,98,98,98,84,84,84,84,84,84,70,70,70,56,56,56,42,42,42,42,42,42,42,42,42,56,70,70,84,98,112,126,154,168,196,210,224,252,266,280,294,322,336,336,364,364,378,392,392,406,420,420,434,434,434,434,434,434,434,434,434,434,420,406,406,392,378,350,336,322,308,294,280,266,252,238,224,210,210,196,196,182,182,182,182,168,168,168,168,168,154,154,154,154,140,140,140,140,140,126,126,126,140,140,140,140,140,140,140,126,126,126,126,126,112,112,112,98,98,98,84,84,84,70,56,56,56,42,42,42,42,42,42,42,42,42,56,56,70,84,98,112,126,140,154,182,196,224,238,266,294,308,322,350,364,392,406,420,420,434,448,462,462,476,476,476,476,476,476,462,462,448,434,420,406,392,378,364,336,322,294,280,252,224,210,196,168,154,140,126,112,98,84,70,56,56,56,42,42,28,28,28,28,28,14,14,14,14,14,14,28,28,28,28,28,28,28,28,28,42,42,42,42,42,28,28,28,28,28,14,14,14,0,0,-14,-14,-14,-28,-28,-28,-42,-42,-42,-42,-42,-42,-42,-28,-28,-28,-14,0,14,28,42,56,84,98,112,140,154,182,210,224,252,266,280,308,322,336,350,364,364,378,378,378,378,378,378,364,350,336,336,322,308,280,266,252,224,196,182,154,126,112,84,56,28,14,-14,-28,-42,-56,-70,-98,-98,-112,-126,-140,-140,-140,-154,-154,-154,-154,-154,-154,-154,-154,-154,-154,-154,-154,-154,-140,-126,-126,-112,-98,-84,-70,-56,-56,-42,-28,-14,-14,0,0,14,14,14,14,14,14,0,0,-14,-14,-14,-28,-28,-42,-42,-42,-56,-56,-56,-56,-56,-42,-42,-42,-42,-28,-28,-14,0,14,28,56,70,84,112,126,140,168,182,196,210,238,238,252,266,280,280,280,294,294,280,280,280,266,252,252,238,224,210,182,168,140,126,98,84,56,28,14,-14,-28,-56,-84,-98,-126,-140,-154,-182,-182,-196,-210,-224,-238,-238,-252,-252,-252,-252,-252,-252,-252,-252,-252,-238,-238,-224,-210,-210,-196,-182,-168,-154,-140,-126,-112,-98,-84,-70,-56,-56,-42,-42,-28,-28,-28,-28,-28,-28,-42,-42,-42,-56,-56,-56,-56,-70,-84,-84,-98,-98,-98,-112,-112,-112,-112,-112,-112,-112,-98,-98,-84,-70,-70,-56,-42,-28,-14,0,28,42,56,70,98,112,126,140,154,154,168,168,182,182,182,182,182,182,168,168,154,140,126,112,98,84,56,42,14,0,-28,-42,-70,-84,-112,-126,-154,-168,-196,-210,-224,-238,-252,-252,-266,-280,-280,-294,-294,-294,-294,-294,-308,-308,-308,-308,-308,-308,-294,-294,-280,-280,-266,-252,-238,-238,-210,-196,-182,-168,-154,-140,-126,-98,-84,-84,-70,-56,-56,-42,-42,-42,-42,-42,-56,-56,-56,-70,-70,-84,-84,-98,-112,-112,-126,-126,-126,-126,-126,-126,-126,-126,-112,-98,-98,-98,-84,-84,-70,-56,-42,-28,-14,0,14,28,42,56,56,84,84,98,112,112,126,126,126,126,126,126,126,112,112,98,84,70,56,42,28,14,0,-14,-28,-56,-70,-84,-98,-112,-126,-140,-154,-168,-182,-196,-210,-210,-224,-238,-238,-238,-252,-252,-252,-252,-252,-252,-252,-238,-238,-224,-224,-210,-196,-196,-182,-168,-154,-126,-112,-98,-84,-56,-42,-28,-14,14,28,28,42,42,56,56,56,56,56,56,56,42,42,28,14,14,0,-14,-14,-28,-28,-42,-42,-42,-56,-56,-56,-56,-56,-56,-42,-42,-42,-28,-14,-14,0,14,28,28,42,56,70,84,98,98,112,126,126,126,140,140,140,140,140,140,140,140,126,126,112,112,98,98,84,70,56,56,42,28,14,14,0,-14,-28,-42,-56,-56,-70,-84,-84,-98,-112,-112,-126,-126,-140,-140,-154,-154,-154,-168,-168,-168,-168,-154,-154,-154,-140,-126,-126,-112,-98,-84,-70,-42,-28,-14,0,14,28,56,56,70,84,84,98,98,98,98,84,84,70,70,56,42,28,28,14,0,-14,-28,-42,-42,-56,-56,-70,-70,-70,-84,-84,-84,-84,-84,-84,-84,-70,-70,-70,-70,-56,-56,-42,-42,-28,-28,-28,-14,-14,-14,0,0,0,14,14,14,14,14,14,14,14,14,14,0,0,0,-14,-14,-28,-28,-42,-42,-42,-56,-56,-70,-70,-70,-84,-84,-84,-98,-98,-98,-112,-112,-112,-112,-126,-126,-126,-126,-126,-126,-126,-126,-126,-126,-126,-112,-98,-98,-84,-84,-70,-56,-42,-28,-14,0,14,14,28,42,42,56,56,56,56,56,56,42,42,28,14,0,-14,-28)
#     wavetf(freq, input, build_tf())
#     return

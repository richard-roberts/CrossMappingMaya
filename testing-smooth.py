import pandas
import numpy
import scipy.signal
import matplotlib.pyplot as plt

# do_plotting = True
do_plotting = False

df = pandas.read_csv("X:/Projects/Facial Retargeting/Blur Video/FACS Richard BW.csv", skipinitialspace=True)

out_data = {}

keys = []

keys += [
    "pose_Tx",
    "pose_Ty",
    "pose_Tz"
]

keys += [
    "pose_Rx",
    "pose_Ry",
    "pose_Rz"
]

keys += [
    "gaze_angle_x",
    "gaze_angle_y",
]

for i in range(68):
    keys += [
        "X_%d" % i,
        "Y_%d" % i,
        "Z_%d" % i
    ]

for i in range(0, 7 + 1):
    keys += [
        "eye_lmk_X_%d" % i,
        "eye_lmk_Y_%d" % i,
        "eye_lmk_Z_%d" % i
    ]

for i in range(28, 35 + 1):
    keys += [
        "eye_lmk_X_%d" % i,
        "eye_lmk_Y_%d" % i,
        "eye_lmk_Z_%d" % i
    ]

for key in keys:
    org = df[key]
    xs = list(range(len(org)))
    fil = scipy.signal.wiener(org, 7, 0.4)

    if do_plotting:
        plt.plot(xs, org, label="Original " + key)
        plt.plot(xs, fil, label="Filtered " + key)
    out_data[key] = fil
 

if do_plotting:
    plt.legend()
    plt.xlim(500, 1000 + 24 * 5)
    plt.show()
else:
    pandas.DataFrame(data=out_data).to_csv("X:/Projects/Facial Retargeting/Blur Video/FACS Richard BW out.csv")
import os

from optostim.common.paths import Paths


def get(name):
    file_path = os.path.abspath(os.path.join(Paths.views(), name))

    if not os.path.exists(file_path):
        raise FileNotFoundError('View {} not found in path {}.'.format(name, file_path))
    return file_path
import os

from optostim.common.paths import Paths


class Resources:

    @staticmethod
    def get(name):
        file_path = os.path.abspath(os.path.join(Paths.resources(), name))

        if not os.path.exists(file_path):
            raise FileNotFoundError('Resource {} not found.'.format(name))
        return file_path

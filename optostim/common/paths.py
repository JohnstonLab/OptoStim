import sys
import os


class Paths:

    camera_images = "Images"

    @staticmethod
    def join(path1, path2):
        return os.path.join(path1, path2)

    @staticmethod
    def main():
        return os.path.abspath(sys.modules['__main__'].__file__)

    @staticmethod
    def root():
        return os.path.dirname(sys.modules['__main__'].__file__)

    @staticmethod
    def resources():
        return os.path.join(Paths.root(), 'resources')

    @staticmethod
    def views():
        return os.path.join(Paths.root(), 'views')


def basename(path):
    return os.path.basename(path)
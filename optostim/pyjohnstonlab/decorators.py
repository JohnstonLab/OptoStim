from functools import wraps

from scipy import misc


class mock_image:

    def __init__(self, path):
        self.path = path
       # self.image = misc.imread(path)

    def __call__(self, func):
        def wrapped_func(obj, frame):
            func(obj, frame)
           # func(obj, self.image)
        return wrapped_func
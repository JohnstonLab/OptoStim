import logging

import numpy as np
from scipy import optimize

log = logging.getLogger(__name__)
# def gaussian(point, amplitude, x0, y0, sigma_x, sigma_y, theta, offset):
#
#     (x, y) = point
#     a = np.cos(theta)**2 / (2 * sigma_x**2) + np.sin(theta)**2 / (2 * sigma_y**2)
#     b = - np.sin(2 * theta) / (4 * sigma_x**2) + np.sin(2 * theta) / (4 * sigma_y**2)
#     c = np.sin(theta)**2 / (2 * sigma_x**2) + np.cos(theta)**2 / (2 * sigma_y**2)
#     f = amplitude * np.exp(-(a * (x - x0)**2 + 2 * b * (x - x0) * (y - y0) + c * (y - y0)**2)) + offset
#     return f.ravel()
#
#
# def fit_gaussian(meshgrid, data, initial_guess=None):
#     if not initial_guess:
#         initial_guess = []
#     popt, pcov = opt.curve_fit(gaussian, meshgrid, data.ravel(), p0=initial_guess)
#     return popt, pcov
#
#
# def numpy_gaussian_2d(x, y, amplitude, x0, y0, sigma_x, sigma_y, theta, offset=0.0):
#     a = np.cos(theta)**2 / (2 * sigma_x**2) + np.sin(theta)**2 / (2 * sigma_y**2)
#     b = - np.sin(2 * theta) / (4 * sigma_x**2) + np.sin(2 * theta) / (4 * sigma_y**2)
#     c = np.sin(theta)**2 / (2 * sigma_x**2) + np.cos(theta)**2 / (2 * sigma_y**2)
#     f = amplitude * np.exp(-(a * (x - x0)**2 + 2 * b * (x - x0) * (y - y0) + c * (y - y0)**2)) + offset
#     return f


class Gaussian:

    def __init__(self, amplitude=0.0, offset=0, width_x=1, width_y=1, rotation=0, x0=0, y0=0):

        self._a = 0
        self._b = 0
        self._c = 0

        self.amplitude = amplitude
        self.offset = offset
        self.width_x = width_x
        self.width_y = width_y
        self.rotation = rotation
        self.x0 = x0
        self.y0 = y0

    def __setattr__(self, key, value):
        try:
            float_value = float(value)
            super().__setattr__(key, float_value)
        except TypeError:
            super().__setattr__(key, value)

    @property
    def parameters(self):
        return [self.amplitude, self.x0, self.y0, self.width_x, self.width_y]

    @parameters.setter
    def parameters(self, new_params):
        self.amplitude = new_params[0]
        self.x0 = new_params[1]
        self.y0 = new_params[2]
        self.width_x = new_params[3]
        self.width_y = new_params[4]
        self.rotation = new_params[5]

    def func(self, scale_x=1, scale_y=1):
        scaled_x0 = scale_x * self.x0
        scaled_y0 = scale_y * self.y0
        scaled_width_x = scale_x * self.width_x
        scaled_width_y = scale_y * self.width_y
        return gaussian(self.amplitude, scaled_x0, scaled_y0, scaled_width_x, scaled_width_y, self.rotation)


def gaussian(height, center_x, center_y, width_x, width_y, rotation):
    """Returns a gaussian function with the given parameters"""
    width_x = float(width_x)
    width_y = float(width_y)

    rotation = np.deg2rad(rotation)
    center_x = center_x * np.cos(rotation) - center_y * np.sin(rotation)
    center_y = center_x * np.sin(rotation) + center_y * np.cos(rotation)

    def rotgauss(x, y):
        xp = x * np.cos(rotation) - y * np.sin(rotation)
        yp = x * np.sin(rotation) + y * np.cos(rotation)
        g = height * np.exp(
            -(((center_x - xp) / width_x) ** 2 +
              ((center_y - yp) / width_y) ** 2) / 2.)
        return g

    return rotgauss


def moments(data):
    """Returns (height, x, y, width_x, width_y)
    the gaussian parameters of a 2D distribution by calculating its
    moments """
    total = data.sum()
    X, Y = np.indices(data.shape)
    x = (X * data).sum() / total
    y = (Y * data).sum() / total
    col = data[:, int(y)]
    width_x = np.sqrt(abs((np.arange(col.size) - y) ** 2 * col).sum() / col.sum())
    row = data[int(x), :]
    width_y = np.sqrt(abs((np.arange(row.size) - x) ** 2 * row).sum() / row.sum())
    height = data.max()
    return height, x, y, width_x, width_y, 0.0


def fitgaussian(data, ftol=1e-3, xtol=1e-3):
    """Returns (height, x, y, width_x, width_y)
    the gaussian parameters of a 2D distribution found by a fit"""
    params = moments(data)
    errorfunction = lambda p: np.ravel(gaussian(*p)(*np.indices(data.shape)) - data)
    result = optimize.least_squares(errorfunction, params, ftol=ftol, xtol=xtol, verbose=0)
    log.debug("Least squares termination code: {}".format(result.status))
    return result.x



import datetime
import logging
import time

import numpy as np
from PyQt5.QtCore import QTimer
from numpy.fft import fft

from .plotting import PyQtGraphWidget

log = logging.getLogger(__name__)

MAX_STORE = 3000
HALF_MAX_STORE = int(MAX_STORE / 2)
ONE_OVER_HALF_MAX_STORE = 1.0 / HALF_MAX_STORE
INVALID_TIME = -1.0


class RespirationRateWidget(PyQtGraphWidget):

    def __init__(self, take_ft_at_seconds=60):
        super().__init__()
        self.take_ft_at_seconds = take_ft_at_seconds
        self.respiration_plot = self.canvas.addPlot(row=0, col=0)
        self.respiration_plot.setTitle("Respiration")

        self.setWindowTitle("Respiration Monitor")

        self.respiration_line = self.respiration_plot.plot(pen="r")

        self.fft_plot = self.canvas.addPlot(row=1, col=0)
        self.fft_plot.setTitle("FFT")
        #self.fft_plot.setYRange(0, 2000, padding=0)
        self.fft_line = self.fft_plot.plot(pen='r')

        self._data = np.zeros((MAX_STORE, ))

        self._time = INVALID_TIME * np.ones((MAX_STORE,))

        self.ft_times = [self.take_ft_at_seconds]
        self.ft_maxes = []

        self.current_index = 0
        self.update_frequency = 20
        self._current_time = 0
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.plot)
        self.plot_timer.setInterval(1000.0/self.update_frequency)
        self.last_time = time.perf_counter()

        self.ft_frequency = np.arange(0, HALF_MAX_STORE, 1) / self.take_ft_at_seconds

    def append(self, t, value):

            in_seconds = t / 1000.0

            self._time[self.current_index] = in_seconds
            self._data[self.current_index] = value
            self._current_time = in_seconds
            self.current_index = (self.current_index + 1) % MAX_STORE

    def hideEvent(self, event):
        self.plot_timer.stop()

    # def update_line(self):
    #     return self._data

    #  todo - FFT does not work when Arduino has a delay. The x and y shapes do not much up. Put on a plaster on it
    #         that causes it to not work after the first time window :(
    def plot(self):

        if self._current_time == 0:
            return

        try:
            self._plot()
        except Exception as e:
            self.dump_data(reason=e.__str__())

    def reset(self):
        self._data = np.zeros_like(self._data)
        self._time = np.zeros_like(self._time)
        self._current_time = 0
        self.current_index = 0

        self.plot()

    def showEvent(self, event):
        self.plot_timer.start()

    def dump_data(self, reason=''):
        time_stamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        filename = "respiration_rate_widget_data_{}.txt".format(time_stamp)

        data = np.vstack((self._time, self._data)).T
        np.savetxt(filename, data, header=reason)

    def _plot(self):

        time_window_start = self._current_time - self.take_ft_at_seconds
        x_min = max(0.0, time_window_start)
        x_max = max(self.take_ft_at_seconds, self._current_time)

        self.respiration_plot.setRange(xRange=[x_min, x_max])

        # copying to avoid potential race conditions from c++ QT timer. See if okay for a while.
        debug_time = self._time.copy()
        debug_data = self._data.copy()

        indices = np.where(np.logical_and(debug_time >= x_min, debug_time <= x_max))
        time = np.take(debug_time, indices[0])
        data = np.take(debug_data, indices[0])
        self.respiration_line.setData(time, data)

        averaged_data = data - np.average(data)

        # interpolate onto uniform t for FFT.
        min_delta_time = np.diff(time).min()
        uniform_time = np.arange(time.min(), time.max(), min_delta_time)
        uniform_data = np.interp(uniform_time, time, averaged_data)

        ft = fft(uniform_data)
        num_samples = ft.shape[0]
        half_num_samples = int(num_samples / 2)
        self.ft_frequency = np.linspace(0.0, 1.0 / (2.0 * min_delta_time), half_num_samples)

        ft_result = (2.0 / num_samples) * np.abs(ft[:half_num_samples])

        self.fft_line.setData(self.ft_frequency, ft_result)

        self.fft_plot.setRange(yRange=[ft_result.min(), ft_result.max()])

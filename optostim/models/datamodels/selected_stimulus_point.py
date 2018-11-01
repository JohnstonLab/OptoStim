from optostim.models.datamodels.pattern import Pattern
from optostim.models.datamodels.stimulus_point import StimulusPoint


class SelectedStimulusPoint:

    def __init__(self, stimulus_point: StimulusPoint, pattern):
        self._check_stimulus_point(stimulus_point)

        self._stimulus_point = stimulus_point

        if not issubclass(pattern, Pattern):
            raise TypeError('pattern is not of pattern type')

        self.pattern = pattern

    def __getstate__(self):
        return {'pattern': self.pattern, 'stimulus_point_index': self.index()}

    def __repr__(self):
        text = 'Selected {} with pattern = {}'
        return text.format(self._stimulus_point, self.pattern)

    def index(self):
        return self._stimulus_point.index

    @property
    def stimulus_point(self):
        return self._stimulus_point

    @stimulus_point.setter
    def stimulus_point(self, value):
        self._check_stimulus_point(value)
        self._stimulus_point = value

    def _check_stimulus_point(self, value):
        if not isinstance(value, StimulusPoint):
            raise ValueError('Value is not of class StimulusPoint.')
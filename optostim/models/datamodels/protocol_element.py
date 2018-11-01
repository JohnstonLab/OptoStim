from enum import IntEnum

from optostim.exceptions import OptoStimValueError
from optostim.models.datamodels.selected_stimulus_point import SelectedStimulusPoint


class ProtocolElementProperty(IntEnum):
    STIMULUSPOINTS = 0
    LASER = 1
    PMT = 2
    SYNC = 3
    WAIT = 4
    DURATION = 5


PROPERTY_FIOS = [
    ProtocolElementProperty.LASER,
    ProtocolElementProperty.PMT,
    ProtocolElementProperty.SYNC,
    ProtocolElementProperty.WAIT,
]


class ProtocolElement:

    # StimulusPoints = 0
    # Laser = 1
    # Pmt = 2
    # Sync = 3
    # Wait = 4
    # Duration = 5

    def __init__(self, selected_stimulus_points=None,
                 laser=False, pmt=False, sync=False, wait=False, duration=0.0):
        self._stimulus_points = selected_stimulus_points if selected_stimulus_points else []
        # self._labjack_state = LabJackStateModel(fio4state=laser, fio5state=pmt, fio6state=sync,
        #                                         fio7state=wait, duration=duration)
        self._laser = laser
        self._pmt = pmt
        self._sync = sync
        self._wait = wait
        self._duration = duration

       # self._

    def __getitem__(self, item):
        if item == ProtocolElementProperty.STIMULUSPOINTS:
            return self.stimulus_points
        elif item == ProtocolElementProperty.LASER:
            return self.laser
        elif item == ProtocolElementProperty.PMT:
            return self.pmt
        elif item == ProtocolElementProperty.SYNC:
            return self.sync
        elif item == ProtocolElementProperty.WAIT:
            return self.wait
        else:
            raise Exception("Can't access protocol element with {}.".format(item))

    def __getstate__(self):
        state = {'duration': self.duration, 'laser': self.laser, 'pmt': self.pmt, 'sync': self.sync, 'wait': self.wait}
        state['stimulus_points'] = [p.__getstate__() for p in self.stimulus_points]
        return state

    def __repr__(self):
        text = 'Protocol Element: Stimulus points = {}, laser = {}, pmt = {}, sync = {}, wait = {}, duration = {}'
        return text.format(self.stimulus_points, self.laser, self.pmt, self.sync, self.wait, self.duration)

    def __setstate__(self, state):
        pass
        # self._laser = state['laser']
        # self._pmt = state['pmt']
        # self._sync = state['sync']
        # self._wait = state['wait']
        # self._duration = state['duration']
     #   pass

    # todo - below is verbose, refactor at some point to be nice and neat, not DRY

    def _check_attribute(self, **kwargs):
        if (True in kwargs.values()) and self.wait:
            raise OptoStimValueError('Wait can not be true at same time as other attributes')
        return True

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, value):
        if self.wait and value > 0.0:
            raise OptoStimValueError('Duration can not be > 0 with wait set to true.')
        self._duration = value

    @property
    def laser(self):
        return self._laser

    @laser.setter
    def laser(self, value):
        self._check_attribute(laser=value)
        self._laser = value

    @property
    def pmt(self):
        return self._pmt

    @pmt.setter
    def pmt(self, value):
        self._check_attribute(pmt=value)
        self._pmt = value

    @property
    def stimulus_points(self):
        return self._stimulus_points

    @stimulus_points.setter
    def stimulus_points(self, value):
        self._check_attribute(stimulus_points=value)
        if not isinstance(value, list):
            raise ValueError('Value is not of list type.')
        if not all(isinstance(item, SelectedStimulusPoint) for item in value):
            raise ValueError('Elements must all be of {} type'.format(SelectedStimulusPoint.__name__))
        self._stimulus_points = value

    @property
    def sync(self):
        return self._sync

    @sync.setter
    def sync(self, value):
        self._check_attribute(sync=value)
        self._sync = value

    @property
    def wait(self):
        try:
            return self._wait
        except AttributeError:
            return False

    @wait.setter
    def wait(self, value):
        if value:
            if (True in [self.laser, self.pmt, self.sync]) or (self.duration > 0.0):
                raise ValueError('Wait can not be set to true when other inputs are true or the duration is > 0.0.')
        self._wait = value
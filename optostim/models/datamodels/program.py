import logging
import random

import cv2
import datetime
import numpy as np
from PyQt5.QtGui import QImage, qRgb

from optostim.models.datamodels.patterns.increment_by_one_pattern import IncrementByOnePattern
from optostim.models.datamodels.patterns.normal_pattern import NormalPattern
from optostim.models.datamodels.patterns.random_pattern import RandomPattern
from optostim.models.datamodels.protocol_element import ProtocolElement
from optostim.models.datamodels.selected_stimulus_point import SelectedStimulusPoint
from pyjohnstonlab.curves import Gaussian

log = logging.getLogger(__name__)

grey_colour_table = [qRgb(i, i, i) for i in range(256)]


class Program(object):

    def __init__(self, image_stack, initial_sequence, pattern, random_seed, stimulus_points, stimulus_widget, loop_count=1,
                 inter_loop_delay=0.0):
        self.images = []
        self.stimulus_points = stimulus_points
        self.initial_sequence = initial_sequence
        self.ild = inter_loop_delay
        self.loop_count = loop_count
        self.image_stack = image_stack
        self.program = None
        self.pattern = pattern
        self.stimulus_widget = stimulus_widget

        random.seed(random_seed)

    def __iter__(self):
        return iter(self.program)

    def __len__(self):
        return len(self.program)

    def __getitem__(self, item):
        return self.program[item]

    def create_new_protocol_sequence(self, previous_protocol_sequence):
        new_protocol_sequence = []

        for protocol_element in previous_protocol_sequence:
            new_protocol_sequence.append(self.new_protocol_element_from_previous(protocol_element))

        return new_protocol_sequence

    def generate(self):
        self.program = [self.initial_sequence]
        for i in range(1, self.loop_count):
            new_protocol_sequence = self.create_new_protocol_sequence(self.program[i - 1])
            self.program.append(new_protocol_sequence)
        # self.generate_images()

    def generate_image(self, loop, iteration, intensity_mask):

        selected_stimulus_points = self.program[loop][iteration].stimulus_points

        if not selected_stimulus_points:
            return None

        img = np.zeros((int(self.image_stack.fov), int(self.image_stack.fov)))
        default_stimulus_colour = 255
        half_dimension_difference = 0.5 * abs(self.stimulus_widget.width() - self.stimulus_widget.height())
        position_translation = [0.0, 0.0]
        position_translation[
            0 if self.stimulus_widget.width() > self.stimulus_widget.height() else 1] = half_dimension_difference

        shortest_scale = min(self.stimulus_widget.width() / self.image_stack.fov,
                             self.stimulus_widget.height() / self.image_stack.fov)

        translation_matrix = np.float32([[1, 0, position_translation[0]],
                                         [0, 1, position_translation[1]]])

        # translation_matrix = np.float32([[shortest_scale, 0, position_translation[0]],
        #                                  [0, shortest_scale, position_translation[1]]])
        # todo - make sure they clip if off the edge? homography probably sorts all this.
        #  Stimulus point positions are not in pixels!

        for selected_stimulus_point in selected_stimulus_points:
            stimulus_point = selected_stimulus_point.stimulus_point
            top_left = (int(round(stimulus_point.top_left[0])),
                        int(round((stimulus_point.top_left[1]))))
            bottom_right = (int(round(stimulus_point.bottom_right[0])),
                            int(round(stimulus_point.bottom_right[1])))
            cv2.rectangle(img, top_left, bottom_right, default_stimulus_colour, cv2.FILLED)

        img = cv2.resize(img, None, fx=shortest_scale, fy=shortest_scale, interpolation=cv2.INTER_NEAREST)

        if intensity_mask.is_set:
            gaussian = intensity_mask.gaussian_fit
            gaussian_scale = min(self.stimulus_widget.width() / intensity_mask.shape[0],
                                 self.stimulus_widget.height() / intensity_mask.shape[1])
            transformed_gaussian = Gaussian(amplitude=gaussian.amplitude,
                                            width_x=gaussian_scale*gaussian.width_x,
                                            width_y=gaussian_scale*gaussian.width_y,
                                            rotation=gaussian.rotation,
                                            x0=gaussian_scale*gaussian.x0,
                                            y0=gaussian_scale*gaussian.y0
                                            )
            meshgrid = np.meshgrid(np.arange(img.shape[0]), np.arange(img.shape[1]))
            mask = transformed_gaussian.func()(meshgrid[1], meshgrid[0])
            img = img * (1.0 - mask / mask.max())

        img = cv2.warpAffine(img, translation_matrix,
                                 (self.stimulus_widget.width(), self.stimulus_widget.height()))
        img = cv2.flip(img, 0)
        return img

    def generated_sequences(self):
        generated_length = len(self.program) - 1
        return self.program[-generated_length:] if generated_length > 0 else []

    def get_image(self, loop, iteration):
        return self.images[loop][iteration] if self.images else None

    @property
    def iterations(self):
        return len(self.program[0]) if self.program else 0

    def new_protocol_element_from_previous(self, protocol_element):

        points_to_add = []
        used_stimulus_points = []
        patterned_points = []

        for point in protocol_element.stimulus_points:
            if point.pattern == NormalPattern:
                points_to_add.append(SelectedStimulusPoint(stimulus_point=point.stimulus_point, pattern=point.pattern))
                used_stimulus_points.append(point.stimulus_point)
            else:
                patterned_points.append(point)

        for point in patterned_points:
            if self.pattern == IncrementByOnePattern:
                found = False
                for i in range(0, len(self.stimulus_points)):
                    next_stimulus_point = self.stimulus_points[(point.index() + 1 + i) % len(self.stimulus_points)]
                    if next_stimulus_point not in used_stimulus_points:
                        found = True
                        break
                assert found, "No stimulus point could be found to increment to"
            elif self.pattern == RandomPattern:
                next_stimulus_point = random.choice([point for point in self.stimulus_points if point not in used_stimulus_points])
                pass
            else:
                raise NotImplementedError('No pattern rules for this pattern exist')
            points_to_add.append(SelectedStimulusPoint(stimulus_point=next_stimulus_point, pattern=point.pattern))
            used_stimulus_points.append(next_stimulus_point)

        points_to_add.sort(key=lambda p: p.stimulus_point.index)

        new_element = ProtocolElement()
        new_element.stimulus_points = points_to_add
        new_element.laser = protocol_element.laser
        new_element.pmt = protocol_element.pmt
        new_element.sync = protocol_element.sync
        new_element.wait = protocol_element.wait
        new_element.duration = protocol_element.duration

        return new_element

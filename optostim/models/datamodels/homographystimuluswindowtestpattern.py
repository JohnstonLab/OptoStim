from enum import Enum

import cv2
import numpy as np

from pyjohnstonlab.mixins import ToQImageMixin


class ShapeTypes(Enum):
    CIRCLE = 0
    PENTAGON = 1
    RECTANGLE = 2
    SQUARE = 3
    TRIANGLE = 4


class HomographyStimulusWindowTestPatternShape:

    def __init__(self, centroid=(0, 0), shape_type=None):
        self.centroid = centroid
        self.shape_type = shape_type


class HomographyStimulusWindowTestPattern(ToQImageMixin):

    def __init__(self):
        self.image = None
        self.shapes = {}

    def generate(self, background_colour, height, shape_colour, width):

        length = min(width, height)

        image = np.ones((length, length), dtype=np.uint8) * background_colour

        dx = int(round(length / 4))
        dy = int(round(length / 3))

        half_width = 100

        centre = (dx, dy)
        point1 = (centre[0] - half_width, centre[1] - half_width)
        point2 = (centre[0] + half_width, centre[1] + half_width)
        cv2.rectangle(image, point1, point2, shape_colour, cv2.FILLED)

        self.shapes[ShapeTypes.SQUARE.name] = \
            HomographyStimulusWindowTestPatternShape(centroid=centre, shape_type=ShapeTypes.SQUARE)

        centre = (2 * dx, dy)
        cv2.circle(image, centre, half_width, shape_colour, cv2.FILLED)
        self.shapes[ShapeTypes.CIRCLE.name] = \
            HomographyStimulusWindowTestPatternShape(centroid=centre, shape_type=ShapeTypes.CIRCLE)

        centre = (dx, 2 * dy)
        point1 = (centre[0] - half_width, centre[1] - 2 * half_width)
        point2 = (centre[0] + half_width, centre[1] + half_width)
        cv2.rectangle(image, point1, point2, shape_colour, cv2.FILLED)
        self.shapes[ShapeTypes.RECTANGLE.name] = \
            HomographyStimulusWindowTestPatternShape(centroid=centre, shape_type=ShapeTypes.RECTANGLE)

        centre = (2 * dx, 2 * dy)
        points = [(centre[0], centre[1] - half_width),
                  (centre[0] - half_width, centre[1] + half_width),
                  (centre[0] + half_width, centre[1] + half_width)]
        cv2.fillPoly(image, np.array([points]), shape_colour)
        self.shapes[ShapeTypes.TRIANGLE.name] = \
            HomographyStimulusWindowTestPatternShape(centroid=centre, shape_type=ShapeTypes.TRIANGLE)

        centre = (3 * dx, 2 * dy)
        delta_angle = 2.0 * np.pi / 5
        points = []
        for i in range(0, 5):
            angle = i * delta_angle
            x = half_width * np.cos(angle) + centre[0]
            y = half_width * np.sin(angle) + centre[1]
            points.append((int(x), int(y)))
        cv2.fillPoly(image, np.array([points]), shape_colour)
        self.shapes[ShapeTypes.PENTAGON.name] =\
            HomographyStimulusWindowTestPatternShape(centroid=centre, shape_type=ShapeTypes.PENTAGON)

        self.image = image

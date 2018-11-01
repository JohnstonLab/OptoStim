from PyQt5 import Qt
from enum import Enum
import logging

import cv2
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QMenu, QAction

from optostim.models.datamodels.homographystimuluswindowtestpattern import HomographyStimulusWindowTestPatternShape, \
    ShapeTypes
from pyjohnstonlab.gui.widgets.camera.cameraframedisplaycontainer import CameraFrameDisplayContainer

log = logging.getLogger(__name__)

GREY = (127, 127, 127)
WHITE = (255, 255, 255)


class ConfirmedShapes:

    def __init__(self):
        self._shapes = {}

    @property
    def shapes(self):
        return self._shapes

    @shapes.setter
    def shapes(self, new_shape):
        self._shapes[new_shape.type] = new_shape
        log.debug(self._shapes)

    @property
    def ready(self):
        for shape in ShapeTypes:
            if shape not in self._shapes:
                return False
        return True


class DetectedShape(HomographyStimulusWindowTestPatternShape):

    def __init__(self, area=0, contours=None):
        super().__init__()
        self.area = area
        self.contours = contours


class ShapeSelectionMenu(QMenu):

    def __init__(self, parent):
        super().__init__(parent)
        for shape in ShapeTypes:
            self.addAction(shape.name)


class ShapeDetectionWidget(CameraFrameDisplayContainer):

    def __init__(self, parent):
        super().__init__(parent)
        self.adaptive_method = cv2.ADAPTIVE_THRESH_MEAN_C
        self.approximation_accuracy = 0.04
        self.block_size = 101
        self.check_position = None
        self.shapes = {}
        self.constant = 0.0
        self.gaussian_filtered_cam_image = None
        self.gaussian_kernel_height = 21
        self.gaussian_kernel_width = 21
        self.gaussian_sigma_width = 0.0
        self.gaussian_sigma_height = 0.0
        self.threshold_cam_image = None

        self.menu = ShapeSelectionMenu(self)
        self.menu.triggered.connect(self.on_menu_triggered)

    def contextMenuEvent(self, event):
        self.menu.exec(event.globalPos())

    def detect_shapes(self, frame):
        self.gaussian_filtered_cam_image = cv2.GaussianBlur(frame,
                                                            (self.gaussian_kernel_height,
                                                             self.gaussian_kernel_width),
                                                            sigmaX=self.gaussian_sigma_width,
                                                            sigmaY=self.gaussian_sigma_height)

        self.threshold_cam_image = cv2.adaptiveThreshold(src=self.gaussian_filtered_cam_image,
                                                         maxValue=255,
                                                         adaptiveMethod=self.adaptive_method,
                                                         thresholdType=cv2.THRESH_BINARY,
                                                         blockSize=self.block_size,
                                                         C=self.constant)

        c = cv2.findContours(self.threshold_cam_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = c[1]

        detected_shapes = [DetectedShape() for _ in range(5)]

        for i, contour in enumerate(contours):
            moments = cv2.moments(contour)
            try:
                centroid_x = int(moments["m10"] / moments["m00"])
                centroid_y = int(moments["m01"] / moments["m00"])
            except ZeroDivisionError:
                continue

            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, self.approximation_accuracy * perimeter, True)
            area = cv2.contourArea(approx)

            min_shape = min(detected_shapes, key=lambda s: s.area)

            if area > min_shape.area and centroid_x != min_shape.centroid[0] and centroid_y != min_shape.centroid[1]:

                if len(approx) == 3:
                    text = 'triangle'
                elif len(approx) == 4:
                    (x, y, w, h) = cv2.boundingRect(approx)
                    aspect_ratio = w / float(h)
                    text = 'square' if aspect_ratio >= 0.95 and aspect_ratio <= 1.05 else 'rectangle'
                elif len(approx) == 5:
                    text = 'pentagon'
                else:
                    text = 'circle'

                min_shape.area = area
                min_shape.centroid = (centroid_x, centroid_y)
                min_shape.type = text
                min_shape.contours = approx

        for shape in detected_shapes:
            if shape.contours is not None:
                cv2.drawContours(self.threshold_cam_image, [shape.contours], -1, GREY, 2)
                cv2.circle(self.threshold_cam_image, shape.centroid, 7, GREY, 2)
                if self.check_position:
                    if cv2.pointPolygonTest(contour=shape.contours, pt=self.check_position[1], measureDist=False) == 1:
                        log.debug("{} is in contour".format(self.check_position[1]))
                        self.shapes[self.check_position[0]] = shape

        for shape_type, shape in self.shapes.items():
            cv2.putText(self.threshold_cam_image, shape_type, shape.centroid, cv2.FONT_HERSHEY_SIMPLEX, 0.5, GREY, 2)

        self.check_position = None
        self.image = self.threshold_cam_image

    @pyqtSlot(QAction)
    def on_menu_triggered(self, action):
        local_pos = self.frameDisplayWidget.mapFromGlobal(self.menu.pos())
        x = local_pos.x() * self.image.width() / self.width()
        y = local_pos.y() * self.image.height() / self.height()
        image_pos = (x, y)

        log.debug("Action: {}, pos: {} Image pos {}".format(action.text(), local_pos, image_pos))
        self.check_position = (action.text(), image_pos)

    def on_customContextMenuRequested(self, position):
        self.menu.exec(QCursor.pos())
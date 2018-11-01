import logging
import os
import time

import cv2
import numpy as np
from PyQt5 import uic
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QFileDialog
from matplotlib import patches

from optostim.common.paths import Paths
from optostim.common.tiff_reader import read_tif
from optostim.widgets.camera_window import CameraWindow

from pyjohnstonlab.gui.message_boxes import question

BUTTON_PRESS_EVENT = 'button_press_event'
BUTTON_RELEASE_EVENT = 'button_release_event'
MOTION_NOTIFY_EVENT = 'motion_notify_event'
PHOTON_IMAGE_SIZE = (1024, 1024)
DEFAULT_POINT_SIZE = 10

log = logging.getLogger(__name__)


def image_data(which_plot):
    return which_plot.get_images()[0].get_array()


class HomographyCameraWidget(CameraWindow):

    def __init__(self, camera_device, camera_image_plot, parent=None):
        super().__init__(camera_device=camera_device, workspace=None, parent=parent)
        self._plot = camera_image_plot
        self.saveImageButton.setText("Send to Homography Window")

    @pyqtSlot()
    def on_saveImageButton_pressed(self):
        log.debug("send to homography")
        time_now = time.localtime()
        self.statusLabel.setText("Sent to homography window at {}".format(time.strftime("%H:%M:%S", time_now)))
        self._plot.clear()
        self._plot.imshow(self.camera.last_image, cmap='gray')
        self._plot.figure.canvas.draw()


class HomographyPoint(QObject):

    pointMoved = pyqtSignal()
    pointRemoved = pyqtSignal(QObject)

    def __init__(self, source, destination, label, parent=None):
        super().__init__(parent)
        self.source = source
        text_offset = source.radius + 3
        self.source_label = source.axes.text(source.center[0] + text_offset, source.center[1], label, color='red',
                                             fontsize=12)
        self.source_label.figure.canvas.draw()

        self.destination = destination
        self.destination_label = destination.axes.text(destination.center[0] + text_offset, destination.center[1],
                                                       label, color='red', fontsize=12)
        self.destination_label.figure.canvas.draw()
        self.dragged_patch = None
        self.press = None
        self._connect()

    @property
    def draw_radius(self):
        return self.source.radius

    @draw_radius.setter
    def draw_radius(self, new_radius):
        radius_change = new_radius -  self.source.get_radius()
        self.source.radius = new_radius
        source_label_position = self.source_label.get_position()
        self.source_label.set_x(source_label_position[0] + radius_change)

        self.destination.radius = new_radius
        destination_label_position = self.destination_label.get_position()
        self.destination_label.set_x(destination_label_position[0] + radius_change)

    def _connect(self):

        canvas = self.source.figure.canvas
        canvas.mpl_connect(BUTTON_PRESS_EVENT, self._on_button_press)
        canvas.mpl_connect(BUTTON_RELEASE_EVENT, self._on_button_release)
        canvas.mpl_connect(MOTION_NOTIFY_EVENT, self._on_motion_notify)

        destination_canvas = self.destination.figure.canvas
        destination_canvas.mpl_connect(BUTTON_PRESS_EVENT, self._on_button_press)
        destination_canvas.mpl_connect(BUTTON_RELEASE_EVENT, self._on_button_release)
        destination_canvas.mpl_connect(MOTION_NOTIFY_EVENT, self._on_motion_notify)

    def _button_pressed_on_patch(self, event, patch):
        if event.inaxes != patch.axes:
            return False
        contains, _ = patch.contains(event)
        if not contains:
            return False
        return True

    def _on_button_press(self, event):

        if event.button == 3 and (self._button_pressed_on_patch(event, self.source) or self._button_pressed_on_patch(event, self.destination)):
            self._remove_point()
            return

        if self._button_pressed_on_patch(event, self.source):
            x, y = self.source.center
            self.press = x, y, event.xdata, event.ydata
            self.dragged_patch = (self.source, self.source_label)
        elif self._button_pressed_on_patch(event, self.destination):
            x, y = self.destination.center
            self.press = x, y, event.xdata, event.ydata
            self.dragged_patch = (self.destination, self.destination_label)

    def _on_button_release(self, event):
        if self.press:
            self.press = None
            patch, _ = self.dragged_patch
            patch.figure.canvas.draw()
            self.pointMoved.emit()

    def _on_motion_notify(self, event):
        if not self.press:
            return
        patch, label = self.dragged_patch
        if event.inaxes != patch.axes:
            return
        x, y, xpress, ypress = self.press
        dx = event.xdata - xpress
        dy = event.ydata - ypress

        patch.center = x + dx, y + dy
        label.set_x(x + dx + patch.radius)
        label.set_y(y + dy)
        patch.figure.canvas.draw()

    def _remove_point(self):
        log.debug("Removing")
        self.destination.remove()
        self.destination_label.remove()

        self.source.remove()
        self.source_label.remove()

        self.pointRemoved.emit(self)


class CameraHomographySetupWidget(QWidget):

    def __init__(self, camera, camera_initialisation, parent=None):
        super().__init__(parent)
        self._camera = camera
        self._camera_initialisation = camera_initialisation
        self._homography_points = []

        uic.loadUi(os.path.join(Paths.views(), 'CameraHomographSetup.ui'), self)

        self.cameraImageWidget.add_navigation_toolbar()
        self.photonImageWidget.add_navigation_toolbar()
        self.warpedImageWidget.add_navigation_toolbar()

        self.cameraImageWidget.canvas.mpl_connect(BUTTON_PRESS_EVENT, self.on_click_camera_image)

        self.cameraImageWidget.figure.suptitle('Camera Image')
        self.camera_image = self.cameraImageWidget.figure.add_subplot(111)
        self._camera_widget = HomographyCameraWidget(camera_device=camera, camera_image_plot=self.camera_image)

        self.photonImageWidget.figure.suptitle('Two Photon Image')
        self.photon_image = self.photonImageWidget.figure.add_subplot(111)

        # self.warpedImageWidget.figure.suptitle('Homography Warped Image')
        self.warped_image = self.warpedImageWidget.figure.add_subplot(211)
        self.warped_image.set_title("Final Result")
        self.absolute_difference_plot = self.warpedImageWidget.figure.add_subplot(212)
        self.absolute_difference_plot.set_title("Absolute Difference Between Warped Camera and Photon Images")

        self._camera.homographyMatrixChanged.connect(self.update_homography_matrix_display)

        self.pointSizeSpinBox.setValue(DEFAULT_POINT_SIZE)

    @pyqtSlot()
    def calculate_homography(self):
        if len(self._homography_points) >= 4:
            log.debug("homography")
            source_points = np.array([p.source.center for p in self._homography_points])
            destination_points = np.array([p.destination.center for p in self._homography_points])

            homography_matrix, status = cv2.findHomography(source_points, destination_points)
            self._camera.homography_matrix = homography_matrix

            destination_size = (image_data(self.photon_image).shape[1], image_data(self.photon_image).shape[0])
            #
            warped_img = cv2.warpPerspective(image_data(self.camera_image), homography_matrix, destination_size)

            self.warped_image.clear()

            diff = np.abs(image_data(self.photon_image) - warped_img)
            self.absolute_difference_plot.imshow(diff, cmap='gray')
            # composed = mask * image_data(self.photon_image) + warped_img

            self.warped_image.imshow(warped_img, cmap='gray')
            self.warped_image.figure.canvas.draw()

    def on_cameraImageButton_pressed(self):
        self._plot_image(self.camera_image)

    def on_cameraFeedButton_pressed(self):
        self._camera_initialisation()
        self._camera_widget.show()

    def on_click_camera_image(self, event):
        if not self.camera_image.images:
            return

        if event.inaxes != self.camera_image or not event.dblclick:
            return

        x = np.round(event.xdata)
        y = np.round(event.ydata)

        self._add_homography_point(x, y)

    def on_deletePointsButton_pressed(self):
        if not question(self, title="Confirm delete points", text="Delete all points?"):
            return

        for point in self._homography_points:
            point._remove_point()
        self._homography_points = []

        self._draw_canvases()

    def on_photonImageButton_pressed(self):
        self._plot_image(self.photon_image, resize=PHOTON_IMAGE_SIZE)

    @pyqtSlot(int)
    def on_pointSizeSpinBox_valueChanged(self, value):
        for point in self._homography_points:
            point.draw_radius = value
        self._draw_canvases()

    def update_homography_matrix_display(self, new_matrix):
        it = np.nditer(new_matrix, flags=['multi_index'])
        while not it.finished:
            i, j = it.multi_index
            matrix_element = getattr(self, "m{}{}".format(i, j))
            matrix_element.setText("{:.2E}".format(new_matrix[i][j]))
            it.iternext()

    def _add_homography_point(self, x, y):

        number = '{}'.format(len(self._homography_points))

        source = self.camera_image.add_patch(patches.Circle((x, y), fc='r', radius=self.pointSizeSpinBox.value()))
        self.camera_image.figure.canvas.draw()

        img_data = image_data(self.camera_image)
        rel_x = x / img_data.shape[1]
        rel_y = y / img_data.shape[0]

        photon_img_data = image_data(self.photon_image)

        photon_x = rel_x * photon_img_data.shape[1]
        photon_y = rel_y * photon_img_data.shape[0]

        destination = self.photon_image.add_patch(patches.Circle((photon_x, photon_y), fc='r',
                                                                 radius=self.pointSizeSpinBox.value()))
        self.photon_image.figure.canvas.draw()

        homography_point = HomographyPoint(source=source, destination=destination, label=number, parent=self)
        homography_point.pointMoved.connect(self.calculate_homography)
        # homography_point.pointRemoved.connect(self._on_homography_point_removed)
        self._homography_points.append(homography_point)
        self.calculate_homography()

    def _plot_image(self, plot, flip=False, resize=None):
        filename = QFileDialog.getOpenFileName(self, "Open image", "", "Image stack (*.*)")

        if not filename[0]:
            return

        if filename[0].endswith(('.tif', '.TIF')):
            try:
                metadata, data, descriptions = read_tif(filename[0])
            except ValueError:
                return
        else:
            data = cv2.imread(filename[0], 0)

        if flip:
            data = cv2.flip(data, 1)
        if resize:
            data = cv2.resize(data, resize)
        plot.imshow(data, cmap='gray')
        plot.figure.canvas.draw()

    # @pyqtSlot(QObject)
    # def _on_homography_point_removed(self, removed_point):
    #     self._homography_points.remove(removed_point)
    #     self._draw_canvases()
    #     self.calculate_homography()

    def _draw_canvases(self):
        self.photon_image.figure.canvas.draw()
        self.camera_image.figure.canvas.draw()

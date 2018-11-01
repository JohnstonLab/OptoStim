import logging

from PyQt5.QtCore import Qt, pyqtSlot, QRectF, QTimer
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QPushButton, QFileDialog, QSlider, \
    QLabel, QSizePolicy, QHBoxLayout, QDoubleSpinBox, QMessageBox
from matplotlib import patches
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle

from pyjohnstonlab.gui.widgets.matplotlib import MatplotlibWidget

PATCH_ALPHA = 0.8
log = logging.getLogger(__name__)


class ScanImageWidget(MatplotlibWidget):

    def __init__(self, model, image_stack, scene, parent=None):
        super().__init__(parent)
        self.stimulate_points_collection = model
        self.axes = None
        self.current_frame = -1
        self.image_stack = image_stack
        self.scene = scene
        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.setFocus()
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.open_button = QPushButton()
        self.open_button.setText('Open image stack')

        self.current_slice_progress_bar = QSlider(Qt.Horizontal)
        self.current_slice_progress_bar.setRange(1, 1)
        self.current_slice_progress_bar.setTickPosition(QSlider.TicksBelow)
        self.current_slice_progress_bar.setTickInterval(1)
        self.current_slice_progress_bar.setEnabled(False)
        self.current_slice_progress_bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.current_frame_label = QLabel()
        self.current_frame_label.setText('0 / 0')
        self.current_frame_label.setAlignment(Qt.AlignCenter)
        self.current_frame_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        label = QLabel()
        label.setText("Simulate point square size")
        self.stimulate_point_width_input = QDoubleSpinBox()
        self.stimulate_point_width_input.setRange(1.0, 2048.0)
        self.stimulate_point_width_input.setValue(self.stimulate_points_collection.size)
        self.stimulate_point_width_input.valueChanged.\
            connect(self.on_stimulate_point_width_input_valueChanged)

        self.clearAllStimuliButton = QPushButton()
        self.clearAllStimuliButton.setText('Clear all stimuli points')

        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)

        self.layout().addWidget(self.current_frame_label)
        self.layout().addWidget(self.current_slice_progress_bar)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(label)
        bottom_layout.addWidget(self.stimulate_point_width_input)
        bottom_layout.addWidget(self.clearAllStimuliButton)
        bottom_layout.addWidget(self.open_button)

        self.layout().addLayout(bottom_layout)

        self.enable_inputs(False)

        self.connect()

    def connect(self):
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.clearAllStimuliButton.pressed.connect(self.on_clearAllStimuliButton_pressed)
        self.current_slice_progress_bar.valueChanged.connect(self.on_slider_valueChanged)
        self.image_stack.dataChanged.connect(self.setup_view)
        self.open_button.pressed.connect(self.on_open_button_pressed)

    def enable_inputs(self, enable):
        self.current_slice_progress_bar.setEnabled(enable)
        self.stimulate_point_width_input.setEnabled(enable)

    @pyqtSlot()
    def on_open_button_pressed(self):
        self.open_image_stack()

    def open_image_stack(self):
        filename = QFileDialog.getOpenFileName(self, "Open image stack", "", "Image stack (*.tif), All Files (*.*)")
        filename = filename[0]
        if filename:
            self.read_in_image(filename=filename)
            self.scene.setSceneRect(0, 0, self.image_stack.width, self.image_stack.height)
            return True
        return False

    def on_stimulate_point_width_input_valueChanged(self, new_value):
        self.stimulate_points_collection.size = new_value
        self.plot_frame(self.current_frame)

    def on_click(self, event):

        if not self.image_stack or not event.inaxes:
            return

        clicked_x = float(event.xdata)
        clicked_y = float(event.ydata)

        centre = (clicked_x, clicked_y)

        if self.stimulate_points_collection.insertRow(self.stimulate_points_collection.rowCount()):
            row = self.stimulate_points_collection.rowCount() - 1

            model_index = self.stimulate_points_collection.index(row, 0)
            self.stimulate_points_collection.setData(model_index=model_index, value=row)

            model_index = self.stimulate_points_collection.index(row, 1)
            self.stimulate_points_collection.setData(model_index=model_index, value=self.current_frame)

            model_index = self.stimulate_points_collection.index(row, 2)
            self.stimulate_points_collection.setData(model_index=model_index, value=centre)

            model_index = self.stimulate_points_collection.index(row, 4)
            self.stimulate_points_collection.setData(model_index=model_index,
                                                     value=self.stimulate_point_width_input.value())

            new_stimulus_point = self.stimulate_points_collection.data[-1]
            width = self.stimulate_point_width_input.value()
            rect = QRectF(-width / 2, -width / 2, width, width)
            brush = QBrush()
            brush.setStyle(Qt.SolidPattern)
            brush.setColor(Qt.white)
            new_stimulus_point.setBrush(brush)
            new_stimulus_point.setRect(rect)
            # self.scene.addItem(new_stimulus_point)
            # new_stimulus_point.setVisible(False)
            new_stimulus_point.setPos(clicked_x, clicked_y)

            self.draw_stimulate_point(new_stimulus_point)
            self.draw_stimulate_point_index(new_stimulus_point)
            self.canvas.draw()

    def on_clearAllStimuliButton_pressed(self):
        reply = QMessageBox().question(self, "Remove all stimuli points",
                                       "Are you sure you wish to clear all stimuli points? ",
                                       QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.stimulate_points_collection.removeRows(0, self.stimulate_points_collection.rowCount())
            self.plot_frame(self.current_frame)

    def draw_stimulate_point(self, stimulus_point):

        size = self.stimulate_points_collection.size
        half_rect_size = size * 0.5

        rect_centre = (stimulus_point.location[0] - half_rect_size, stimulus_point.location[1] - half_rect_size)

        patch = self.axes.add_patch(
            patches.Rectangle(
                rect_centre,
                size,
                size,
                facecolor='w',
                edgecolor='k',
                alpha=PATCH_ALPHA
            )
        )

    def draw_stimulate_points(self, axes):

        rects = []
        current_frame_rects = []

        size = self.stimulate_points_collection.size
        half_rect_size = size * 0.5

        for point in self.stimulate_points_collection:
            rect_corner = (point.location[0] - half_rect_size, point.location[1] - half_rect_size)
            rect = Rectangle(rect_corner, size, size)
            current_frame_rects.append(rect) if point.frame == self.current_frame else rects.append(rect)
            self.draw_stimulate_point_index(stimulus_point=point)

        other_frame_patches = PatchCollection(rects, facecolors='k', edgecolors='b', alpha=PATCH_ALPHA)
        axes.add_collection(other_frame_patches)

        current_frame_patch_collection = PatchCollection(current_frame_rects, facecolors='w', edgecolors='b', alpha=PATCH_ALPHA)
        axes.add_collection(current_frame_patch_collection)

        self.canvas.draw()

    def draw_stimulate_point_index(self, stimulus_point):
        text_offset = 5
        text_y_offset = stimulus_point.location[1] + 0.5 * self.stimulate_points_collection.size + text_offset
        self.axes.text(stimulus_point.location[0], text_y_offset, stimulus_point.index, color='green', fontsize=15)

    @property
    def has_image(self):
        return True if self.image_stack.filename else False

    @pyqtSlot()
    def on_slider_valueChanged(self):
        self.plot_frame(self.current_slice_progress_bar.value())
#        self.stimulus_widget.setScene(self.scenes[self.current_slice_progress_bar.value()])

    def read_in_image(self, filename):
        self.image_stack.filename = filename
        self.setup_view()

    def plot_frame(self, frame_number):

        if frame_number < 1 or (frame_number > self.image_stack.dimensions[0]):
            return

        if len(self.image_stack.dimensions) == 2:
            self.plot(self.image_stack.data[:, :])
            self.current_frame_label.setText('1 / 1')
            self.current_frame = frame_number
        elif self.image_stack.headers:
            self.current_slice_progress_bar.setValue(frame_number)
            self.current_frame_label.setText('{0} / {1}'.format(frame_number, self.image_stack.dimensions[0]))
            self.plot(data=self.image_stack.data[frame_number - 1, :, :])
                      #extent=(0, self.image_stack.fov, self.image_stack.fov, 0))
            self.current_frame = frame_number
        else:
            self.plot(data=self.image_stack.data)

    def plot(self, data, extent=None):
        self.axes = self.figure.add_subplot(111)
        self.axes.clear()

        # todo - turn off anti-aliasing? Change the interpolation type
        img = self.axes.imshow(data, clim=(data.min(), data.max()), extent=extent)
        self.draw_stimulate_points(self.axes)
        self.canvas.draw()

    def setup_view(self):
        self.plot_frame(frame_number=1)
        self.current_slice_progress_bar.setMaximum(self.image_stack.dimensions[0])
        self.current_slice_progress_bar.setEnabled(True)
        self.enable_inputs(True)

    def showEvent(self, event):
        self.plot_frame(frame_number=self.current_frame)

    def wheelEvent(self, wheel_event):
        if self.image_stack is None:
            return
        angle = wheel_event.angleDelta().y()
        self.plot_frame(self.current_frame + 1) if angle > 0 else self.plot_frame(self.current_frame - 1)

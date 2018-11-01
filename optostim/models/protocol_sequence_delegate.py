import logging

from PyQt5.QtCore import Qt, QPoint, QSize, QPointF, QRectF
from PyQt5.QtGui import QFontMetrics, QPixmap
from PyQt5.QtWidgets import QStyledItemDelegate, QStyle

from optostim.common.resources import Resources
from optostim.models.datamodels.selected_stimulus_point import SelectedStimulusPoint
from optostim.models.itemmodels.protocol_sequence import ProtocolSequence

log = logging.getLogger(__name__)


class ProtocolSequenceDelegate(QStyledItemDelegate):

    # todo - little bug where row height does not update first time

    def __init__(self, parent=None):
        super().__init__(parent)
        self.container_height = 0

    def paint(self, painter, option, model_index):

        if model_index.column() == 0:
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            self._paint_stimulus_points_cell(painter, option, model_index)
        elif model_index.column() == 4:
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            self._paint_wait_icon(painter, option, model_index)

        else:
            super().paint(painter, option, model_index)

    def _paint_wait_icon(self, painter, option, model_index):

        pixmap = model_index.data(Qt.DecorationRole)

        if pixmap:
            draw_pixmap_top_left_x = option.rect.x() + 0.5 * option.rect.width() - 0.5 * pixmap.width()
            draw_pixmap_top_left_y = option.rect.y() + 0.5 * option.rect.height() - 0.5 * pixmap.height()

            top_left = QPoint(draw_pixmap_top_left_x, draw_pixmap_top_left_y)
            painter.drawPixmap(top_left, pixmap)

    def _debug_draw(self, painter, option, model_index):

        num_points = 9

        font_metrics = QFontMetrics(option.font)

        pixmap = QPixmap()
        pixmap.load(Resources.get('dice.png'))

        padding = 1

        max_img_height = pixmap.height()

        cell_centre = (option.rect.x() + 0.5 * option.rect.width(), option.rect.y() + 0.5 * option.rect.height())

        font_height = font_metrics.height()

        container_height = font_height + max_img_height + 2 * padding
        container_width = pixmap.width() + 2 * padding

        start_x = cell_centre[0] - container_width * (num_points / 2)

        painter.drawLine(QPointF(cell_centre[0], 0), QPointF(cell_centre[0], option.rect.height()))
        painter.drawLine(QPointF(0, cell_centre[1]), QPointF(option.rect.width(), cell_centre[1]))

        container = QRectF(start_x, cell_centre[1] - 0.5 * container_height, container_width,
                           container_height)

        for i in range(0, num_points):
            painter.drawRect(container)

            painter.drawPixmap(container.topLeft().x() + padding, container.topLeft().y() + padding, pixmap)

            text = str(i)
            text_bounding_rect = font_metrics.boundingRect(text)
            painter.drawText(container.center().x() - 0.5 * text_bounding_rect.width(), container.bottomLeft().y() - padding, text)

            container.translate(container_width, 0)


    def _paint_stimulus_points_cell(self, painter, option, model_index):

        points = model_index.data(role=ProtocolSequence.Roles.STIMULUS_POINTS.value)

        if points:

            font_metrics = QFontMetrics(option.font)
            font_height = font_metrics.height()

            pixmap_plus1 = QPixmap()
            pixmap_plus1.load(Resources.get('one.png'))

            pixmap_random = QPixmap()
            pixmap_random.load(Resources.get('dice.png'))

            padding = 1

            max_img_height = max(pixmap_plus1.height(), pixmap_random.height())
            max_img_width = max(pixmap_plus1.width(), pixmap_random.width())

            cell_centre = (option.rect.x() + 0.5 * option.rect.width(), option.rect.y() + 0.5 * option.rect.height())

            container_height = font_height + max_img_height + 2 * padding
            container_width = max_img_width + 2 * padding

            start_x = cell_centre[0] - container_width * (len(points) / 2)

            container = QRectF(start_x, cell_centre[1] - 0.5 * container_height, container_width,
                               container_height)

            self.container_height = max(self.container_height, container.height())

            for point in points:
                pixmap = point.pattern.pixmap(max_img_height)
                painter.drawPixmap(container.topLeft().x() + padding, container.topLeft().y() + padding, pixmap)

                text = str(point.index())
                text_bounding_rect = font_metrics.boundingRect(text)
                painter.drawText(container.center().x() - 0.5 * text_bounding_rect.width(),
                                 container.bottomLeft().y() - padding, text)

                container.translate(container_width, 0)

            self.sizeHintChanged.emit(model_index)







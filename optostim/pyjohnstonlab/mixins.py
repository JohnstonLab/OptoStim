from pathlib import Path

from PyQt5 import uic
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QRadioButton, QDoubleSpinBox

UI_FILE_LOCATIONS = {

}

QT_CONTROLS_MAPPING = {
    QRadioButton: 'isChecked',
    QDoubleSpinBox: 'value'
}


class LoadUIFileMixin(object):

    ui_view_name = None

    def load_ui(self):
        p = Path(__file__).parents[1]
        view_location = p.joinpath('views/' + self.get_view_name() + '.ui').__str__()

        uic.loadUi(view_location, self)

    def get_view_name(self):
        return self.ui_view_name if self.ui_view_name else self.__class__.__name__

    def get_input(self, name, suffix=None):
        _suffix = suffix if suffix else 'Input'
        try:
            input_object = getattr(self, name + _suffix)
        except AttributeError:
            exception_message = 'Could not get input for {0}. Is there a control named \'{0}{1}\'?'.format(name, _suffix)
            raise AttributeError(exception_message)

        control_method = getattr(input_object, QT_CONTROLS_MAPPING[type(input_object)])
        return control_method()


class JSONPickleMixin:

    save_attributes = []

    def __getnewargs__(self):
        return ('pickled',)

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        if 'pickled' in args:
            instance.__init__()
        return instance

    def __getstate__(self):
        state = self.__dict__.copy()
        if self.save_attributes:

            to_save = {}
            for key, value in state.items():
                if key in self.save_attributes:
                    to_save[key] = value
            return to_save
        else:
            return state

    def __setstate__(self, state):
        self.__dict__ = state.copy()


class ToQImageMixin:

    def get_image(self):
        return self.image

    def to_qimage(self):
        img = self.get_image()
        return QImage(img.data, img.shape[1], img.shape[0], img.strides[0], QImage.Format_Grayscale8)

    @property
    def qimage(self):
        return self.to_qimage()
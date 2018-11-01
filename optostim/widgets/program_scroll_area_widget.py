from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy

from optostim.widgets.program_element import ProgramElement


class ProgramScrollAreaWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.master_program_element = ProgramElement(loop_number=1, parent=self)
        self.program_element_widgets = [self.master_program_element]

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Program"))
        layout.addWidget(self.master_program_element)
        layout.addStretch(10)
        self.setLayout(layout)

    def set_model(self, model):
        self.master_program_element.setup_tableview(model)

    def set_number_of_widgets(self, models, number):

        if number < 1:
            raise ValueError('Can\'t have less than one loop count widget.')

        if number < len(self.program_element_widgets):

            extra_widgets = len(self.program_element_widgets) - number

            for i in range(0, extra_widgets):
                widget = self.program_element_widgets.pop()
                self.layout().removeWidget(widget)
                widget.deleteLater()

        elif number > len(self.program_element_widgets):

            widgets_to_add = number - len(self.program_element_widgets)

            for i in range(0, widgets_to_add):
                loop_number = len(self.program_element_widgets)
                widget = ProgramElement(loop_number=loop_number + 1, parent=self)
                widget.setup_tableview(models[loop_number], draggable=False)
                self.program_element_widgets.append(widget)
                self.layout().insertWidget(self.layout().count() - 1, widget)
        else:
            self.update_current_widgets(new_models=models)

        self.update()

    def update_current_widgets(self, new_models):
        for i in range(1, len(self.program_element_widgets)):
            self.program_element_widgets[i].update_model(new_model=new_models[i])






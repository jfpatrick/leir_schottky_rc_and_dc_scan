from qtpy.QtWidgets import QCheckBox, QHBoxLayout
from comrad import CPropertyEditWidgetDelegate
import numpy as np


class MyWidgetDelegate(CPropertyEditWidgetDelegate):

    def create_widget(self, field_id, item_type, editable, user_data, parent):
        if field_id == 'enableChannel':
            self.check_box_l: QCheckBox = QCheckBox()
            self.check_box_h: QCheckBox = QCheckBox()
            self.check_box_v: QCheckBox = QCheckBox()

            self.check_box_layout: QHBoxLayout = QHBoxLayout()
            self.check_box_layout.addWidget(self.check_box_l)
            self.check_box_layout.addWidget(self.check_box_h)
            self.check_box_layout.addWidget(self.check_box_v)
            return self.check_box_layout
        else:
            widget = super().create_widget(field_id=field_id, item_type=item_type, editable=editable,
                                           user_data=user_data, parent=parent)
            return widget

    def read_value(self, send_only_updated):
        res = super().read_value(send_only_updated)
        try:
            res['enableChannel'] = np.array([self.check_box_l.isChecked(), self.check_box_h.isChecked(),
                                             self.check_box_v.isChecked(), False])
        except KeyError:
            pass
        return res

    def display_data(self, field_id, value, user_data, item_type, widget):

        try:
            if field_id == 'enableChannel':
                self.check_box_l.setChecked(value[0])
                self.check_box_h.setChecked(value[1])
                self.check_box_v.setChecked(value[2])
            elif field_id == 'acqTriggerDelay':
                widget.setValue(value)
            elif field_id == 'acqWindowLength':
                widget.setValue(value)
            elif field_id == 'spcmSamplingFrequency':
                widget.setCurrentIndex(widget.findText(value.label))

        except KeyError:
            pass

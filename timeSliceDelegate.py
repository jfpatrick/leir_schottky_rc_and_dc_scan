from PyQt5.QtWidgets import QSlider
from comrad import Signal, QWidget


class TimeSliceDelegate(QWidget):

    def __init__(self, widget=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.time_slice_widget = widget
        self.slider_step = 2

        # Initialize some values
        min_value = 10
        max_value = 100
        current_value = 50

        self.time_slice_widget.horizontalSlider.setMinimum(min_value)
        self.time_slice_widget.horizontalSlider.setMaximum(max_value)
        self.time_slice_widget.horizontalSlider.setValue(current_value)
        self.time_slice_widget.horizontalSlider.setTickPosition(QSlider.TicksBelow)
        self.time_slice_widget.horizontalSlider.setTickInterval(5)
        self.time_slice_widget.slider_current_val.setText(str(current_value))
        self.time_slice_widget.slider_min_val.setText(str(min_value))
        self.time_slice_widget.slider_max_val.setText(str(max_value))
        self.time_slice_widget.horizontalSlider.valueChanged.connect(self.update_current_slider_value)

        self._set_current_slider_value.connect(self.time_slice_widget.slider_current_val.setText)

    _set_current_slider_value = Signal(str)

    def update_current_slider_value(self):
        self._set_current_slider_value.emit(str(self.time_slice_widget.horizontalSlider.value()))

    def update_horizontal_slider_limits(self, c_time):
        time_slice_first = c_time[0]
        time_slice_end = c_time[-1]
        step = len(c_time)

        if self.time_slice_widget.slider_min_val != time_slice_first:
            self.time_slice_widget.horizontalSlider.setMinimum(time_slice_first)
            self.time_slice_widget.slider_min_val.setText(str(time_slice_first))
        if self.time_slice_widget.slider_max_val != time_slice_end:
            self.time_slice_widget.horizontalSlider.setMaximum(time_slice_end)
            self.time_slice_widget.slider_max_val.setText(str(time_slice_end))
        if self.slider_step != step:
            self.time_slice_widget.horizontalSlider.setSingleStep(step)

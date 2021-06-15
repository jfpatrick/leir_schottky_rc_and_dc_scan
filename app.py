import functools
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QMessageBox
import numpy as np
from typing import Tuple, Optional, Iterator, Dict
from comrad import (CDisplay, Signal,
                    CChannelData)

from listernerWidget import ListenerWidget
from plot_power_spectrum import Plot_Power_Spectrum
from timeSliceDelegate import TimeSliceDelegate
from updaterWidget import UpdaterWidget
from property_field import RAMP_CAV, DEBUNCH_CAV, SET_POINT_START, SET_POINT_END
from property_field import FFTACQUISITION, FIELD_PSD, FIELD_C_TIME, FIELD_P_AVE, FIELD_P_RMS, FIELD_FREQ_START, \
    FIELD_FREQ_RES, FIELD_FREQ_THEO
from property_field import SETTINGS, FIELD_GAMMA_REL, FIELD_M0, FIELD_SLIP_FACTOR, FIELD_HARMONIC
from plot_p_mean_p_rms_scan_param import Plot_P_Mean_P_Rms_Dpp0_Scan_Param


class DemoDisplay(CDisplay):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.power_spectrum_src = Plot_Power_Spectrum(plot_height=10)
        self.plot_p_data_and_scan_params = Plot_P_Mean_P_Rms_Dpp0_Scan_Param(plot_height=10)

        canvas_psd, canvas_psd_time_slice = self.power_spectrum_src.get_canvas()
        self.plot_utils_layout_1: QHBoxLayout = QHBoxLayout()
        self.plot_utils_layout_1.addWidget(canvas_psd)
        self.plot_utils_layout_1.addWidget(canvas_psd_time_slice)

        self.dummy_widget_1: QWidget = QWidget()
        self.dummy_widget_1.setLayout(self.plot_utils_layout_1)

        # Create object to handle plotting of p_mean, p_rms, dppp0 and scan parameters
        canvas_scan_param, canvas_p, canvas_dpp0 = self.plot_p_data_and_scan_params.get_canvas()
        self.plot_utils_layout_2: QHBoxLayout = QHBoxLayout()
        self.plot_utils_layout_2.addWidget(canvas_scan_param)
        self.plot_utils_layout_2.addWidget(canvas_p)

        self.dummy_widget_2: QWidget = QWidget()
        self.dummy_widget_2.setLayout(self.plot_utils_layout_2)

        self.plot_utils_layout_3: QHBoxLayout = QHBoxLayout()
        self.plot_utils_layout_3.addWidget(canvas_dpp0)

        self.dummy_widget_3: QWidget = QWidget()
        self.dummy_widget_3.setLayout(self.plot_utils_layout_3)

        self.verticalLayout.insertWidget(0, self.dummy_widget_2)
        self.verticalLayout.insertWidget(1, self.dummy_widget_3)
        self.verticalLayout.insertWidget(2, self.dummy_widget_1)

        # Accessing the CEmbdedDisplay with the time sice selection slider
        self.timeSliceDelegate = TimeSliceDelegate(self.time_slice_selection.embedded_widget)
        # Accessing the CEmbeddedDisplay select_variable to see what the user wants to plot
        plot_variable = self.select_variable.embedded_widget.comboBox_variable_to_select.currentText()
        self.define_variable_to_plot(plot_variable)
        self.select_variable.embedded_widget.comboBox_variable_to_select.currentIndexChanged.connect(
            self.on_click_comboBox)

        self._set_updated_lower_scan_value_ramp.connect(self.ramp_ph_st.setText)
        self._set_updated_upper_scan_value_ramp.connect(self.ramp_ph_en.setText)
        self._set_updated_lower_scan_value_debunch.connect(self.debunch_ph_st.setText)
        self._set_updated_upper_scan_value_debunch.connect(self.debunch_ph_en.setText)

        # Update start buttons
        self._set_enable_start_scan_button_ramp.connect(self.ramp_start.setEnabled)
        self._set_enable_start_scan_button_debunch.connect(self.debunch_start.setEnabled)
        self._set_enable_interrupt_scan_button_ramp.connect(self.ramp_interrupt.setEnabled)
        self._set_enable_interrupt_scan_button_debunch.connect(self.debunch_interrupt.setEnabled)

        # Scan machinery
        self.ramp_updater = UpdaterWidget(parent=self, init_channel=RAMP_CAV)
        self.debunch_updater = UpdaterWidget(parent=self, init_channel=DEBUNCH_CAV)
        self.ramp_listener = ListenerWidget(parent=self, init_channel=RAMP_CAV)
        self.debunch_listener = ListenerWidget(parent=self, init_channel=DEBUNCH_CAV)
        self.iterator_listener_fftAcq = ListenerWidget(parent=self, init_channel=FFTACQUISITION)
        self.iterator_listener_settings = ListenerWidget(parent=self, init_channel=SETTINGS)

        self.phase_counter = 0
        self.is_first_scan_acquisition = False
        self.remaining_scans: Optional[Iterator[Tuple[int, int]]] = None
        self.iterations_per_scan = -1
        self.original_phases: Dict[str, Tuple[int, int]] = {}
        self.is_scanning: Optional[str] = None  # 'ramp', 'debunch', or None
        self.ramp_listener.value_acquired.connect(functools.partial(self.phase_values_updated, key='ramp'))
        self.debunch_listener.value_acquired.connect(functools.partial(self.phase_values_updated, key='debunch'))
        self.iterator_listener_fftAcq.value_acquired.connect(self.scan_value_updated)
        self.iterator_listener_settings.value_acquired.connect(self.settings_value_updated)
        self.ramp_start.clicked.connect(functools.partial(self.start_scan, key='ramp'))
        self.debunch_start.clicked.connect(functools.partial(self.start_scan, key='debunch'))
        self.ramp_interrupt.clicked.connect(self.interrupt_scan)
        self.debunch_interrupt.clicked.connect(self.interrupt_scan)

        self.average_p = []
        self.rms_p = []
        self.y_average_p = []
        self.y_average_p_pos = []
        self.y_average_p_neg = []
        self.tot_dsp = None
        self.x_axis_pcolormesh_init = 1
        self.scan_is_interrupted = False

        self.slip_factor = 0.0
        self.harmonic = 0.0
        self.m_0 = 0.0
        self.gamma_rel = 0.0

    _set_updated_lower_scan_value_ramp = Signal(str)
    _set_updated_upper_scan_value_ramp = Signal(str)
    _set_updated_lower_scan_value_debunch = Signal(str)
    _set_updated_upper_scan_value_debunch = Signal(str)
    _set_enable_start_scan_button_ramp = Signal(bool)
    _set_enable_start_scan_button_debunch = Signal(bool)
    _set_enable_interrupt_scan_button_ramp = Signal(bool)
    _set_enable_interrupt_scan_button_debunch = Signal(bool)

    def ui_filename(self):
        return 'app.ui'

    def define_variable_to_plot(self, plot_variable):
        if plot_variable ==  'Frequency':
            self.frequency = True
            self.momentum = False
            self.dpp = False
        if plot_variable == 'Momentum':
            self.frequency = False
            self.momentum = True
            self.dpp = False
        if plot_variable == 'Dp/p':
            self.frequency = False
            self.momentum = False
            self.dpp = True

    def on_click_comboBox(self):
        plot_variable = self.select_variable.embedded_widget.comboBox_variable_to_select.currentText()
        self.define_variable_to_plot(plot_variable)

    def settings_value_updated(self, packet: CChannelData):
        self.slip_factor = packet.value[FIELD_SLIP_FACTOR]
        self.harmonic = packet.value[FIELD_HARMONIC]
        self.m_0 = packet.value[FIELD_M0]
        self.gamma_rel = packet.value[FIELD_GAMMA_REL]

    def scan_value_updated(self, packet: CChannelData):
        # Get psd data and analyse it and send it to plot all the time, whether a scan is requested or not
        # dpp0_for_a_single_acquisition: is always the same vector once the Schottky parameters are fixed
        dpp0_for_a_single_acquisition, indx_to_plot = self.analyse_data(packet)
        if self.iterations_per_scan != -1:
            self.phase_counter += 1
            self.average_p.append(packet.value[FIELD_P_AVE][indx_to_plot])
            self.rms_p.append(packet.value[FIELD_P_RMS][indx_to_plot])
            psd = packet.value[FIELD_PSD]
            psd_slice = psd[indx_to_plot:indx_to_plot + 1, :]
            x_axis_pcolormesh = np.arange(0, self.x_axis_pcolormesh_init + 1, 1)
            if self.is_first_scan_acquisition:
                self.tot_dsp = psd_slice.copy()
                self.is_first_scan_acquisition = False
            else:
                try:
                    self.tot_dsp = np.concatenate((self.tot_dsp, psd_slice), axis=0)
                except Exception:
                    print("Exception = ", Exception)
                    return
            self.x_axis_pcolormesh_init += 1
            dpp0 = np.array(dpp0_for_a_single_acquisition)

            if self.phase_counter >= self.iterations_per_scan:
                # Every time a scan step is finished, i.e after self.iterations_per_scan, the code comes here
                # From here we instruct plot_power_spectrum to make the average of all acquired values during a
                # scan step and plot it
                mask_nan_ave_p = np.ma.array(self.average_p, mask=np.isnan(self.average_p))
                mask_nan_rms_p = np.ma.array(self.rms_p, mask=np.isnan(self.rms_p))
                average_p_for_one_step = np.average(mask_nan_ave_p)/1e3 # Plot GeV/c
                rms_p_for_one_step = np.average(mask_nan_rms_p)/1e3 # Plot GeV/c
                self.y_average_p.append(average_p_for_one_step)
                self.y_average_p_pos.append(average_p_for_one_step + rms_p_for_one_step)
                self.y_average_p_neg.append(average_p_for_one_step - rms_p_for_one_step)
                if self.scan_is_interrupted is not True:
                    self.plot_p_data_and_scan_params.update_p_mean_rms_and_dpp0_plots(self.y_average_p,
                                                                             self.y_average_p_pos,
                                                                             self.y_average_p_neg,
                                                                             dpp0,
                                                                             self.tot_dsp,
                                                                             x_axis_pcolormesh)
                self.phase_counter = 0
                # Clear self.average_p and self.rms_p for the next step
                self.average_p = []
                self.rms_p = []
                if self.scan_is_interrupted:
                    key = self.is_scanning
                    # print("Original phases = ", key, self.original_phases[key])
                    phase_start, phase_end = self.original_phases[key]
                    updater = getattr(self, f'{key}_updater')
                    # print("For the moment the updated is commented, the values that will be sent are = ", phase_start, phase_end)
                    updater.update_signal.emit({
                        SET_POINT_START: phase_start,
                        SET_POINT_END: phase_end,
                    })
                    self.is_scanning = False
                    self.scan_is_interrupted = False
                    self.x_axis_pcolormesh_init = 1
                    self.iterations_per_scan = -1
                    self.initialize_arrays()
                    self.is_first_scan_acquisition = False
                    self.update_start_scan_buttons(True)
                else:
                    self.issue_new_scan_settings()

    def phase_values_updated(self, packet: CChannelData, key: str):
        if not self.is_scanning:
            self.original_phases[key] = packet.value[SET_POINT_START], packet.value[SET_POINT_END]
            # print("Original phases = ", key, self.original_phases[key])

    def start_scan(self, key: str):
        alert = QMessageBox.question(self, "Message",
                                     "Before starting the scan make sure the SEND DATA TO NXCALS "
                                     "is ticked if you want to log the data. Do you want to start the scan?",
                                     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                     QMessageBox.Cancel)

        if alert == QMessageBox.No:
            return
        if alert == QMessageBox.Cancel:
            return

        self.is_scanning = key

        phase_start_field = getattr(self, f'{self.is_scanning}_ph_st')
        phase_end_field = getattr(self, f'{self.is_scanning}_ph_en')
        phase_step_field = getattr(self, f'{self.is_scanning}_step')
        phase_num_acq = getattr(self, f'{self.is_scanning}_num_acq')
        try:
            lower = float(phase_start_field.text())
            upper = float(phase_end_field.text())
            step = float(phase_step_field.text())
            self.iterations_per_scan = int(phase_num_acq.text())
            self.is_first_scan_acquisition = True
            self.x_axis_pcolormesh_init = 1
            if lower > upper:
                lower = float(phase_end_field.text())
                upper = float(phase_start_field.text())
                set_updated_lower_scan_value = getattr(self, f'_set_updated_lower_scan_value_{self.is_scanning}')
                set_updated_upper_scan_value = getattr(self, f'_set_updated_upper_scan_value_{self.is_scanning}')
                set_updated_lower_scan_value.emit(str(lower))
                set_updated_upper_scan_value.emit(str(upper))

            def iterate_phases(lower: float, upper: float, step: float):
                for i in np.arange(lower, upper + step, step):
                    yield i, i

            self.remaining_scans = iterate_phases(lower, upper, step)
            # HERE FIRST SCAN STEP IS SENT
            self.plot_p_data_and_scan_params.initialize_plots()
            self.plot_p_data_and_scan_params.initialize_x_scan_axis()
            self.issue_new_scan_settings()
            self.update_start_scan_buttons(False)
            self.update_interrupt_scan_button(False)

        except ValueError:
            QMessageBox.warning(self.parentWidget(), 'Invalid input', 'Your input does not appear to be a number type')

    def interrupt_scan(self):
        alert = QMessageBox.question(self, "Message",
                                     "Do you really want to interrupt the scan? ",
                                     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                     QMessageBox.Cancel)

        if alert == QMessageBox.No:
            return
        if alert == QMessageBox.Cancel:
            return
        if alert == QMessageBox.Yes:
            self.scan_is_interrupted = True

    def issue_new_scan_settings(self):
        if self.remaining_scans is None or not self.is_scanning:
            self.iterations_per_scan = -1
            self.is_first_scan_acquisition = False
            self.x_axis_pcolormesh_init = 1
            self.initialize_arrays()
            if self.is_scanning: self.update_start_scan_buttons(True)
            return
        try:
            phase_start, phase_end = next(self.remaining_scans)
            # print("Remaining scans = ", phase_start, phase_end)
            self.plot_p_data_and_scan_params.update_scan_parameters_plot(phase_start, self.is_scanning)
        except StopIteration:
            self.update_start_scan_buttons(True)
            key = self.is_scanning
            # print("Original phases = ", key, self.original_phases[key])
            self.remaining_scans = None
            self.iterations_per_scan = -1
            self.is_first_scan_acquisition = False
            self.x_axis_pcolormesh_init = 1
            self.initialize_arrays()

            try:
                phase_start, phase_end = self.original_phases[key]
                # print("Setting original phases now = ", phase_start
                #       , phase_end)
            except KeyError:
                pass
            else:
                updater = getattr(self, f'{self.is_scanning}_updater')
                # print("For the moment the updated is commented, the values that will be sent are = ", phase_start, phase_end)
                updater.update_signal.emit({
                    SET_POINT_START: phase_start,
                    SET_POINT_END: phase_end,
                })
        else:
            updater = getattr(self, f'{self.is_scanning}_updater')
            # print("For the moment the updated is commented, the values that will be sent are = ", phase_start, phase_end)
            updater.update_signal.emit({
                SET_POINT_START: phase_start,
                SET_POINT_END: phase_end,
            })

    def initialize_arrays(self):
        self.y_average_p = []
        self.y_average_p_pos = []
        self.y_average_p_neg = []
        self.tot_dsp = None
        self.x_axis_pcolormesh_init = 1

    def analyse_data(self, packet: CChannelData):
        freq_start = packet.value[FIELD_FREQ_START]
        freq_res = packet.value[FIELD_FREQ_RES]
        psd = packet.value[FIELD_PSD]
        c_time = packet.value[FIELD_C_TIME]
        to_MHz = 1e6
        freq_theo = packet.value[FIELD_FREQ_THEO] / to_MHz
        dpp_o = []
        value_to_plot = []
        indx_time_slice_to_plot = 0
        if len(c_time) != 0:
            self.timeSliceDelegate.update_horizontal_slider_limits(c_time)
            # self.update_horizontal_slider_limits(c_time)
            freq_start = freq_start / to_MHz
            freq_res = freq_res / to_MHz
            freq_end = freq_start + ((psd.shape[1] + 1) * freq_res)
            freq = np.linspace(freq_start, freq_end, psd.shape[1] + 1, endpoint=True)
            c_time = np.append(c_time, c_time[-1] + (c_time[-1] - c_time[-2]))
            time_slice_to_plot = int(self.time_slice_selection.embedded_widget.horizontalSlider.value())
            indx_time_slice_to_plot = np.abs(c_time - time_slice_to_plot).argmin()

            if self.slip_factor != 0.0 and self.harmonic != 0.0:
                dpp_o = 1000 * (1 / self.slip_factor) * (((freq / self.harmonic) - freq_theo) / freq_theo)
                dpp_o = dpp_o[::-1]
                if self.frequency:
                    value_to_plot = freq/self.harmonic
                if self.momentum:
                    value_to_plot = 2 * np.pi * 12.5 * self.m_0 * self.gamma_rel * (freq/self.harmonic) / (3e8 * 1e3)  # To get MeV/c
                if self.dpp:
                    value_to_plot = 1000 * (1 / self.slip_factor) * (((freq / self.harmonic) - freq_theo) / freq_theo)
                    value_to_plot = value_to_plot[::-1]
                self.power_spectrum_src.update_psd_plots(value_to_plot, c_time, psd, indx_time_slice_to_plot,
                                                         self.frequency, self.momentum, self.dpp)
        else:
            print("Not valid data published by Schottky, waiting for valid data")

        return dpp_o, indx_time_slice_to_plot

    def update_start_scan_buttons(self, status: bool):
        self._set_enable_start_scan_button_ramp.emit(status)
        self._set_enable_start_scan_button_debunch.emit(status)
        if status:
            self._set_enable_interrupt_scan_button_debunch.emit(status)
            self._set_enable_interrupt_scan_button_ramp.emit(status)

    def update_interrupt_scan_button(self, status: bool):
        if self.is_scanning == 'ramp':
            self._set_enable_interrupt_scan_button_debunch.emit(status)
        else:
            self._set_enable_interrupt_scan_button_ramp.emit(status)

import matplotlib.pyplot as plt
from accwidgets.graph import UpdateSource
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
import numpy as np
from mplCanvas import MplCanvas


class Plot_P_Mean_P_Rms_Dpp0_Scan_Param(UpdateSource):

    def __init__(self, plot_height, *args, **kwargs):
        super().__init__(*args, **kwargs)
        np.random.seed(19680801)
        Z = np.random.rand(6, 10)
        x = np.arange(-0.5, 10, 1)
        y = np.arange(4.5, 11, 1)
        self.slip_factor = 0.0
        self.harmonic = 0.0
        self.time_slice_to_plot = 50

        self.sc3 = MplCanvas(self, width=5, height=plot_height, dpi=80)
        self.sc3.set_title_name("Scan parameters = f(scan step)")
        self.sc3.axes1.plot([1, 2, 3, 4], [1, 4, 9, 18], 'r+')
        self.sc3.draw()

        self.sc4 = MplCanvas(self, width=5, height=plot_height, dpi=80)
        self.sc4.set_title_name("$\hat{p}$ and p$_{RMS}$ = f(scan step)")
        self.sc4.axes1.plot([1, 2, 3, 4], [17, 10, 5, 1], 'r+')
        self.sc4.draw()

        self.sc5 = MplCanvas(self, width=5, height=plot_height, dpi=80)
        self.sc5.set_title_name('$\Delta$p/p$_0$ (per mill) = f(scan step)(p$_0$ ~ 18.3 GeV/c = p*Q)')
        self.sc5.axes1.pcolormesh(x, y, Z)
        self.sc5.draw()

        self.init_x_scan_axis = 0
        self.y_scan_parameters = []
        self.x_scan_steps = []
        self.tot_dsp = None
        self.first_dsp = None

    def get_canvas(self):
        return self.sc3, self.sc4, self.sc5

    def update_scan_parameters_plot(self, current_value, cavity):
        self.init_x_scan_axis = self.init_x_scan_axis + 1
        self.y_scan_parameters.append(current_value)
        self.x_scan_steps.append(self.init_x_scan_axis)
        self.sc3.axes1.cla()
        self.sc3.axes1.plot(self.x_scan_steps, self.y_scan_parameters, 'b+')
        self.sc3.axes1.set_xlabel('Scan step')
        self.sc3.axes1.set_ylabel('{:} phase (deg)'.format(cavity))
        self.sc3.draw()

    def update_p_mean_rms_and_dpp0_plots(self,
                                         y_average_p,
                                         y_average_p_pos,
                                         y_average_p_neg,
                                         y_average_dpp0,
                                         tot_dsp_slice,
                                         x_axis):
        self.sc4.axes1.cla()
        self.sc4.axes1.plot(self.x_scan_steps, y_average_p, 'r+')
        self.sc4.axes1.plot(self.x_scan_steps, y_average_p_pos, 'g')
        self.sc4.axes1.plot(self.x_scan_steps, y_average_p_neg, 'g')

        self.sc4.axes1.set_xlabel('Scan step')
        self.sc4.axes1.set_ylabel('$\hat{p}$ and p$_{RMS}$ (GeV/c)')
        self.sc4.draw()

        self.sc5.axes1.cla()
        levels = MaxNLocator(nbins=15).tick_values(tot_dsp_slice.min(), tot_dsp_slice.max())
        cmap = plt.get_cmap('PiYG')
        norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)
        print("Inside power_spectrum = ", x_axis.shape,  np.array(y_average_dpp0).shape, tot_dsp_slice.shape)
        self.sc5.axes1.pcolormesh(x_axis, np.array(y_average_dpp0), tot_dsp_slice.T, cmap=cmap, norm=norm)
        self.sc5.axes1.set_xlabel('Scan progress for the selected time slice, here all acquisitions are shown')
        self.sc5.axes1.set_ylabel('$\Delta$p/p$_0$ (per mill)')
        self.sc5.draw()

    def initialize_plots(self):
        self.y_scan_parameters = []
        self.x_scan_steps = []

    def initialize_x_scan_axis(self):
        self.init_x_scan_axis = 0

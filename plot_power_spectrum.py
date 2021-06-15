import matplotlib.pyplot as plt
from accwidgets.graph import UpdateSource
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
import numpy as np

from mplCanvas import MplCanvas


class Plot_Power_Spectrum(UpdateSource):

    def __init__(self, plot_height, *args, **kwargs):
        super().__init__(*args, **kwargs)
        np.random.seed(19680801)
        Z = np.random.rand(6, 10)
        x = np.arange(-0.5, 10, 1)
        y = np.arange(4.5, 11, 1)
        self.slip_factor = 0.0
        self.harmonic = 0.0
        self.time_slice_to_plot = 50
        # Create the plots
        self.sc1 = MplCanvas(self, width=5, height=plot_height, dpi=80)
        self.sc1.set_title_name('$\Delta$p/p$_0$ (per mill) (p$_0$ ~ 18.3 GeV/c = p*Q)')
        im = self.sc1.axes1.pcolormesh(x, y, Z)
        self.sc1.draw()

        self.sc2 = MplCanvas(self, width=5, height=plot_height, dpi=80)
        self.sc2.set_title_name("$\Delta$p/p$_0$ (per mill) (p$_0$ ~ 18.3 GeV/c = p*Q)")
        N_points = 100000
        n_bins = 20
        x_hist = np.random.randn(N_points)
        self.sc2.axes1.hist(x_hist, bins=n_bins)
        self.sc2.draw()

    def get_canvas(self):
        return self.sc1, self.sc2

    def update_psd_plots(self, dpp_o, c_time, psd, indx_time_slice_to_plot, frequency, momentum, dpp):
        self.sc1.axes1.cla()
        self.sc2.axes1.cla()
        levels = MaxNLocator(nbins=200).tick_values(psd.min(), psd.max())
        cmap = plt.get_cmap('GnBu') #"GnBu", 'PiYG'
        norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)
        if frequency:
            y_label_title = 'frequency (MHz)'
        if momentum:
            y_label_title = 'p (GeV/c) (p$_0$ ~ 18.3 GeV/c = p*Q)'
        if dpp:
            y_label_title = '$\Delta$p/p$_0$ (per mill) (p$_0$ ~ 18.3 GeV/c = p*Q)'
        im = self.sc1.axes1.pcolormesh(dpp_o, c_time, psd, shading='auto', cmap=cmap, norm=norm)
        # if first_time:
        #     self.sc1.fig.colorbar(im, ax=self.sc1.axes1)
        self.sc1.axes1.set_ylabel('Acq Window (ms)')
        self.sc1.axes1.set_xlabel(y_label_title)
        self.sc1.draw()
        dpp_o = np.delete(dpp_o, dpp_o.shape[0] - 1)
        self.sc2.axes1.plot(dpp_o, psd[indx_time_slice_to_plot, :])
        self.sc2.axes1.set_xlabel(y_label_title)
        self.sc2.draw()


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=6, dpi=80):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes1 = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)

    def set_title_name(self, title):
        self.axes1.set_title(title, fontsize=15)


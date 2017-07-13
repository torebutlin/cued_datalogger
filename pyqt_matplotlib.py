import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import QSizePolicy


class MatplotlibCanvas(FigureCanvas):
    def __init__(self):
        matplotlib.use('Qt5Agg')  
        matplotlib.rcParams['toolbar'] = 'None'

        fig = Figure()
        self.axes = fig.add_subplot(111)
        self.axes.hold(False)
        self.init_plot()
        
        FigureCanvas.__init__(self, fig)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def init_plot(self):
        pass
    
    def draw_plot(self):
        pass
    
    def update_plot(self):
        pass
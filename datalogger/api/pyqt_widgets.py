from PyQt5.QtCore import pyqtSignal, Qt
import numpy as np

# ------------------------------------------------------
# Basic PyQt Widgets
# ------------------------------------------------------
from PyQt5.QtWidgets import QSlider, QSpinBox, QVBoxLayout, QHBoxLayout, QWidget

class BaseNControl(QWidget):
    """
    A QWidget containing a paired SpinBox and Slider that are constrained to 
    show values in a given base.
    
    Attributes
    ----------
    valueChanged : pyqtSignal(int)
        The signal emitted when the current value is changed, containing the 
        current value.
    orientation : Qt.Vertical or Qt.Horizontal
        The orientation of the SpinBox - Slider pair
    base : int
        The current base that the BaseNControl is using.
    """
    valueChanged = pyqtSignal(int)
    
    def __init__(self, orientation, parent=None, 
                 show_spinbox=True, 
                 show_slider=True,
                 base=2):
        
        super().__init__(parent)
        
        self.parent = parent
        self.orientation = orientation
        self.base = base
        
        self.spinbox = BaseNSpinBox(self)
        self.slider = QSlider(self.orientation, self)
        
        # Update whenever enter is pressed in the spinbox
        self.spinbox.editingFinished.connect(self.on_spinbox_edit_finished)
        # Update when the buttons are pressed
        self.spinbox.sig_step_down.connect(self.decrease_value)
        self.spinbox.sig_step_up.connect(self.increase_value)
        # Update whenever the slider is moved
        self.slider.valueChanged.connect(self.set_n)
        #self.slider.actionTriggered.connect(self.on_slider_value_changed)
        
        if self.orientation == Qt.Vertical:
            layout = QVBoxLayout()
        elif self.orientation == Qt.Horizontal:
            layout = QHBoxLayout()
        else:
            raise ValueError("Unrecognised orientation (accepted values: "
                "Qt.Horizontal, Qt.Vertical)")
        
        if show_spinbox:
            layout.addWidget(self.spinbox)
        if show_slider:
            layout.addWidget(self.slider)
        
        self.setLayout(layout)
    
    def set_power_range(self, min_power_n, max_power_n):    
        """Set the range of allowed values to be from ``base**min_power_n`` to
        ``base**max_power_n``."""
        self.slider.setRange(min_power_n, max_power_n)
        self.spinbox.setRange(self.base**min_power_n, self.base**max_power_n)
        
        self.set_n(min_power_n)
    
    def set_value_range(self, min_value, max_value):
        """Set the range of allowed values to be from *min_value* to 
        *max_value*."""
        self.spinbox.setRange(min_value, max_value)
        min_n = int(np.floor(np.log(min_value)/np.log(self.base)))
        max_n = int(np.ceil(np.log(max_value)/np.log(self.base)))
        self.slider.setRange(min_n, max_n)
        
        self.set_n(min_n)

    def set_n(self, n, set_both=False):
        """If *n* is in range, set it as the current n-value.
        
        If *set_both*, set the values for both the slider and spinbox, 
        otherwise set the value for whichever did not send the signal."""
        if n >= self.slider.minimum() and n <= self.slider.maximum(): 
            self.n = n
            if set_both:
                self.spinbox.setValue(self.base**self.n)
                self.slider.setValue(self.n)
            elif self.sender() == self.slider:
                self.spinbox.setValue(self.base**self.n)
            elif self.sender() == self.spinbox:
                self.slider.setValue(self.n)     
            self.valueChanged.emit(self.base**self.n)

    def set_value(self, value):
        """Set the value for the slider and the spinbox to *value*."""
        n = int(np.round(np.log(value)/np.log(self.base)))
        self.set_n(n, True)
        
    def increase_value(self):
        self.set_n(self.n + 1, True)
        
    def decrease_value(self):
        self.set_n(self.n - 1, True)
    
    def on_spinbox_edit_finished(self):
        self.set_value(self.spinbox.value())
    
    def value(self):
        """Return the current value of the BaseNControl."""
        return self.spinbox.value()
        

class BaseNSpinBox(QSpinBox):
    
    sig_step_up = pyqtSignal()
    sig_step_down = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def stepBy(self, number_of_steps):
        if number_of_steps > 0:
            self.sig_step_up.emit()
        elif number_of_steps < 0:
            self.sig_step_down.emit()

# -----------------------------------------
# Matplotlib widgets
# -----------------------------------------
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import QSizePolicy


class MatplotlibCanvas(FigureCanvas):
    """A custom version of Matplotlib's :class:`FigureCanvas`, with a title, no
    toolbar, and Qt resizable functionality."""
    def __init__(self, suptitle=None):
        matplotlib.use('Qt5Agg')  
        matplotlib.rcParams['toolbar'] = 'None'

        fig = Figure()
        fig.suptitle(suptitle)
        self.axes = fig.add_subplot(111)

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

from matplotlib.cm import get_cmap

def matplotlib_lookup_table(name):
    """Return a pyqtgraph-style lookup table (*ndarray*) from a 
    :class:`~/matplotlib.colors.Colormap`"""
    cmap = get_cmap(name)
    return cmap(np.arange(256)) * 255
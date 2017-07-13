import numpy as np

from matplotlib.cm import get_cmap
from matplotlib.colors import Colormap

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui

class SimpleColormap(Colormap):
    def __init__(self, name):
        self.cmap = get_cmap(name)
        super().__init__(name)
    
    def to_rgb(self, x):
        return np.asarray(self.cmap(x)) * 255


def plot_contours(x, y, Z, num_contours=32, contour_spacing=1e-3):
    # Create the plot widget     
    plot = pg.plot()
    plot.setXRange(0, x.max())
    plot.setYRange(0, y.max())
    
    # We need to convert from x and y being in 'samples' to being in 'units'.
    # Currently the values of Z will just be plotted on axes where the scale
    # is the (i, j) position of the value in Z.
    # We want to plot them on axes where the scale is x, y.
    # To do this we use a QTransform matrix
    samples_to_units = QtGui.QTransform()
    # Scale factor to map the largest sample number to the largest unit
    x_scale_fact = x.max() / x.size
    y_scale_fact = y.max() / y.size
    # Set the values in the transformation matrix
    samples_to_units.scale(x_scale_fact, y_scale_fact)
    
    # Create a colour map for colouring the contours
    cmap = SimpleColormap("jet")

    # Iterate through all the contours    
    for i in np.linspace(0, 1, num_contours):
        level = i*contour_spacing
        # Create the contour at the specified level
        curve = pg.IsocurveItem(level=level, data=Z.transpose(), pen=cmap.to_rgb(i))
        # Transform it 
        curve.setTransform(samples_to_units)
        # Add it to the plot
        plot.addItem(curve)

    return plot


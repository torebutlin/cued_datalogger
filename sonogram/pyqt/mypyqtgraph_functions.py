import numpy as np

from matplotlib.cm import get_cmap
from matplotlib.colors import Colormap

import pyqtgraph as pg
from pyqtgraph import PlotWidget
from pyqtgraph.Qt import QtGui


class SimpleColormap(Colormap):
    def __init__(self, name):
        self.cmap = get_cmap(name)
        super().__init__(name)
    
    def to_rgb(self, x):
        return np.asarray(self.cmap(x)) * 255


class ContourMapPlot(PlotWidget):
    def __init__(self, x, y, Z, num_contours=32, contour_spacing=1e-3, cmap="jet"):
        self.x = x
        self.y = y
        self.Z = Z
        self.num_contours = num_contours
        self.contour_spacing = contour_spacing
        self.cmap = SimpleColormap(cmap)
        
        self.update_scale_fact()
        
        super().__init__()
        # Calculate the initial contours
        self.update_map()
                 
    def update_map(self, show_contours=False):
        self.setXRange(0, self.x.max() * 1.01)
        self.setYRange(0, self.y.max() * 1.01)
        
        # Clear the current screen
        self.clear()
        
        if show_contours:
            for i in np.linspace(0, 1, self.num_contours):
                level = i*self.contour_spacing
                # Create the contour with a given colour
                contour = pg.IsocurveItem(pen=self.cmap.to_rgb(i))
                # Set the data for the contour at the specified level
                contour.setData(self.Z.transpose(), level=level)
                # Transform it to the correct unit scale
                contour.setTransform(self.samples_to_units)
                self.addItem(contour)
        else:
            colorplot = pg.ImageItem(self.Z.transpose())
            colorplot.setTransform(self.samples_to_units)
            colorplot.setLookupTable(self.cmap.to_rgb(np.arange(256)))
            self.addItem(colorplot)

    def update_scale_fact(self):
        # We need to convert from x and y being in 'samples' to being in 'units'.
        # Currently the values of Z will just be plotted on axes where the scale
        # is the (i, j) position of the value in Z.
        # We want to plot them on axes where the scale is x, y.
        # To do this we use a QTransform matrix
        self.samples_to_units = QtGui.QTransform()
        # Scale factor to map the largest sample number to the largest unit
        self.x_scale_fact = self.x.max() / self.x.size
        self.y_scale_fact = self.y.max() / self.y.size
        # Set the values in the transformation matrix
        self.samples_to_units.scale(self.x_scale_fact, self.y_scale_fact)

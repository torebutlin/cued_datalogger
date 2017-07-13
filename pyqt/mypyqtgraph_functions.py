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


class ContourMap(PlotWidget):
    def __init__(self, x, y, Z, num_contours=32, contour_spacing=1e-3, cmap="jet"):
        self.x = x
        self.y = y
        self.Z = Z
        self.num_contours = num_contours
        self.contour_spacing = contour_spacing
        self.cmap = SimpleColormap(cmap)
        
        self.update_scale_fact()
        
        super().__init__()
        self.init_plot()
   
    def init_plot(self):
        # Set the plot properties
        self.setXRange(0, self.x.max() * 1.01)
        self.setYRange(0, self.y.max() * 1.01)
        
        # Calculate the initial contours
        self.initialise_contours()
        self.update_contours()
 
    def initialise_contours(self):
        self.contours = []
        # Iterate through all the contours    
        for i in np.linspace(0, 1, self.num_contours):
            # Create the contour with a given colour
            contour = pg.IsocurveItem(pen=self.cmap.to_rgb(i))
            # Add it to the contour structure
            self.contours.append(contour)
        
        # Add all the contours to the plot
        for contour in self.contours:
            self.addItem(contour)
             
    def update_contours(self):
        self.setXRange(0, self.x.max() * 1.01)
        self.setYRange(0, self.y.max() * 1.01)
        
        for i, val in enumerate(np.linspace(0, 1, self.num_contours)):
            level = val*self.contour_spacing
            # Set the data for the contour at the specified level
            self.contours[i].setData(self.Z.transpose(), level=level)
            # Transform it to the correct unit scale
            self.contours[i].setTransform(self.samples_to_units)

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


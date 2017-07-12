import numpy as np
from matplotlib.cm import get_cmap
from matplotlib.colors import Colormap
import pyqtgraph as pg


class SimpleColormap(Colormap):
    def __init__(self, name):
        self.cmap = get_cmap(name)
        super().__init__(name)
    
    def to_rgb(self, x):
        return np.asarray(self.cmap(x)) * 255


def plot_contours(Z, X=None, Y=None, num_contours=32, contour_spacing=1e-3):      
    plot = pg.plot()
    
    img = pg.ImageItem(np.zeros_like(Z))
    plot.addItem(img)
    
    cmap = SimpleColormap("jet")

    for i in np.linspace(0, 1, num_contours):
        level = i*contour_spacing
        curve = pg.IsocurveItem(level=level, data=Z.transpose(), pen=cmap.to_rgb(i))
        curve.setParentItem(img)


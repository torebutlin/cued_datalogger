import numpy as np
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout


# External functions ----------------------------------------------------------
def to_dB(x):
    """A simple function that converts x to dB"""
    return 20*np.log10(x)


def from_dB(x):
    """A simple function that converts x in dB to a ratio over 1"""
    return 10**(x/20)


def func(w, wr, zr, c):
    """A modal peak"""
    return c / (wr**2 - w**2 + 2j * zr * wr**2)


def func_abs(w, wr, zr, c):
    """A modal peak"""
    return np.abs(c / (wr**2 - w**2 + 2j * zr * wr**2))


def circle_fit(data):
    # Take the real and imaginary parts
    x = data.real
    y = data.imag

    # Use the method from "Theoretical and Experimental Modal Analysis" p221
    # Set up the matrices
    xs = np.sum(x)
    ys = np.sum(y)
    xx = np.square(x).sum()
    yy = np.square(y).sum()
    xy = np.sum(x*y)
    L = data.size
    xxx = np.sum(x*np.square(x))
    yyy = np.sum(y*np.square(y))
    xyy = np.sum(x*np.square(y))
    yxx = np.sum(y*np.square(x))

    A = np.asarray([[xx, xy, -xs],
                    [xy, yy, -ys],
                    [-xs, -ys, L]])

    B = np.asarray([[-(xxx + xyy)],
                    [-(yyy + yxx)],
                    [xx + yy]])

    # Solve the equation
    v = np.linalg.solve(A, B)

    # Find the circle parameters
    x0 = v[0]/-2
    y0 = v[1]/-2
    R0 = np.sqrt(v[2] + x0**2 + y0**2)
    return x0, y0, R0


def plot_circle(x0, y0, R0):
    theta = np.linspace(-np.pi, np.pi, 180)
    x = x0[0] + R0[0]*np.cos(theta)
    y = y0[0] + R0[0]*np.sin(theta)
    return x, y


def find_closest_value(array, value):
    """Find closest item in array to value"""
    idx = (np.abs(array-value)).argmin()
    return array[idx]


# Circle Fit window -----------------------------------------------------------
class CircleFitWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        # # Transfer function plot
        self.transfer_func_plot_w = pg.PlotWidget(title="Transfer Function",
                                                  labels={'bottom': ("Frequency", "rad"),
                                                          'left': ("Transfer Function", "dB")})
        self.transfer_func_plot = self.transfer_func_plot_w.getPlotItem()

        # # Region Selection plot
        self.region_select_plot_w = pg.PlotWidget(title="Region Selection",
                                                  labels={'bottom': ("Frequency", "rad"),
                                                          'left': ("Transfer Function", "dB")})
        self.region_select_plot = self.region_select_plot_w.getPlotItem()
        # Region
        self.init_roi()
        self.region_select_plot.addItem(self.roi)

        self.roi.sigRegionChanged.connect(self.update_zoom)
        self.roi.sigRegionChanged.connect(self.update_plots)
        self.transfer_func_plot.sigXRangeChanged.connect(self.update_roi)
        self.transfer_func_plot.sigXRangeChanged.connect(self.update_plots)

        # # Nyquist plot
        self.nyquist_plot_w = pg.PlotWidget(title="Nyquist plot",
                                            labels={'bottom': ("Re"),
                                                    'left': ("Im")})
        self.nyquist_plot = self.nyquist_plot_w.getPlotItem()

        # # Circle plot
        self.circle_plot_w = pg.PlotWidget(title="Circle fit",
                                           labels={'bottom': ("Re"),
                                                   'left': ("Im")})
        self.circle_plot = self.circle_plot_w.getPlotItem()

        # # Fit plot
        self.fit_plot_w = pg.PlotWidget(title="Fitted peak",
                                        labels={'bottom': ("Frequency", "rad"),
                                                          'left': ("Transfer Function", "dB")})
        self.fit_plot = self.fit_plot_w.getPlotItem()

        # # Layout
        plots = QGridLayout()
        plots.addWidget(self.transfer_func_plot_w, 0, 0)
        plots.addWidget(self.region_select_plot_w, 0, 1)
        plots.addWidget(self.nyquist_plot_w, 1, 0)
        plots.addWidget(self.circle_plot_w, 1, 1)
        plots.addWidget(self.fit_plot_w, 2, 0, 1, 2)
        self.setLayout(plots)

        self.setWindowTitle('Circle fit')
        self.show()

    def init_roi(self):
        self.roi = pg.ROI([0, 0], pen='r')
        # Horizontal scale handles
        self.roi.addScaleHandle([1, 0.5], [0, 0.5])
        self.roi.addScaleHandle([0, 0.5], [1, 0.5])
        # Vertical scale handles
        self.roi.addScaleHandle([0.5, 0], [0.5, 1])
        self.roi.addScaleHandle([0.5, 1], [0.5, 0])
        # Corner scale handles
        self.roi.addScaleHandle([1, 1], [0, 0])
        self.roi.addScaleHandle([0, 0], [1, 1])

    def update_zoom(self):
        self.w_min, self.a_min = self.roi.pos()
        self.w_max, self.a_max = self.roi.pos() + self.roi.size()
        self.transfer_func_plot.setXRange(self.w_min, self.w_max, padding=0)
        self.transfer_func_plot.setYRange(self.a_min, self.a_max, padding=0)

    def update_roi(self):
        region = np.asarray(self.transfer_func_plot.getViewBox().viewRange())
        self.roi.setPos(region[:, 0])
        self.roi.setSize(region[:, 1] - region[:, 0])

    def update_plots(self):
        # Get zoomed in region
        self.get_viewed_region()

        # Update Nyquist plot
        self.nyquist_plot.clear()
        self.nyquist_plot.plot(self.a_reg.real, self.a_reg.imag, pen=None,
                               symbol='o', symbolPen=None, symbolBrush='r')

        """ TEMA METHOD: """
        # Recalculate circle
        self.x0, self.y0, self.R0 = circle_fit(self.a_reg)
        self.x_c, self.y_c = plot_circle(self.x0, self.y0, self.R0)

        """ ITERATIVE METHOD: """
        # Recalculate circle
        wr, zr, c = self.fit_peak()
        self.fit_plot.clear()
        self.fit_plot.plot(w, np.abs(to_dB(self.a)))
        self.fit_plot.plot(w, np.abs(to_dB(func(self.w, wr, zr, c))))

        # Update plot
        self.circle_plot.clear()
        # Plot the data
        self.circle_plot.plot(self.a_reg.real, self.a_reg.imag, pen=None,
                              symbol='o', symbolPen=None, symbolBrush='r')
        # Plot the circle
        self.circle_plot.plot(self.x_c, self.y_c,
                              pen=pg.mkPen('w', width=2, style=QtCore.Qt.DashLine))

    def get_viewed_region(self):
        # Get just the peak we're looking at
        self.wmin, self.wmax = self.transfer_func_plot.getAxis('bottom').range
        self.amin, self.amax = self.transfer_func_plot.getAxis('left').range
        # Convert back to linear scale
        self.amin = from_dB(self.amin)
        self.amax = from_dB(self.amax)

        lower_w = np.where(self.w > self.wmin)[0][0]
        upper_w = np.where(self.w < self.wmax)[0][-1]
        lower_a = np.where(self.a > self.amin)[0][0]
        upper_a = np.where(self.a < self.amax)[0][-1]

        if lower_w > lower_a:
            lower = lower_w
        else:
            lower = lower_a
        if upper_w < upper_a:
            upper = upper_w
        else:
            upper = upper_a

        self.a_reg = self.a[lower:upper]
        self.w_reg = self.w[lower:upper]

    def fit_peak(self):
        self.get_viewed_region()
        self.a_reg_abs = np.abs(self.a_reg)

        # # Find initial parameters for curve fitting
        # Find where the peak is
        i = np.where(self.a_reg_abs == self.a_reg_abs.max())[0][0]
        wr0 = self.w_reg[i]  # Resonant freq guess
        c0 = self.a_reg_abs[i]  # Modal constant guess

        # 3dB points
        # find the values
        a3dB = from_dB(to_dB(c0) - 3)
        a3dB_below = find_closest_value(self.a_reg_abs[:i], a3dB)
        a3dB_above = find_closest_value(self.a_reg_abs[i:], a3dB)
        # Find where they are in the array
        i_a3dB_below = np.where(self.a_reg_abs == a3dB_below)[0][0]
        i_a3dB_above = np.where(self.a_reg_abs == a3dB_above)[0][0]

        z0 = (self.w_reg[i_a3dB_above] - self.w_reg[i_a3dB_below]) / (2 * wr0)  # Damping guess

        popt, pcon = curve_fit(self.modal_peak_abs, self.w_reg, self.a_reg_abs,
                               p0=[wr0, z0, c0])
        self.wr = popt[0]
        self.zr = popt[1]
        self.c = popt[2]

        return self.wr, self.zr, self.c

    def modal_peak(self, w, wr, zr, c):
        """A modal peak - complex"""
        return c / (wr**2 - w**2 + 2j * zr * wr**2)

    def modal_peak_abs(self, w, wr, zr, c):
        """A modal peak - magnitude"""
        return np.abs(c / (wr**2 - w**2 + 2j * zr * wr**2))

    def set_data(self, w=None, a=None):
        if a is not None:
            self.a = a
        if w is not None:
            self.w = w
        else:
            pass
        self.transfer_func_plot.plot(x=self.w, y=to_dB(np.abs(self.a)))
        self.region_select_plot.plot(x=self.w, y=to_dB(np.abs(self.a)))


def plot_this_peak(circle_fit_widget):
    wr, zr, c = circle_fit_widget.fit_peak()
    plt.plot(w, to_dB(a))
    plt.plot(w, to_dB(func(w, wr, zr, c)))


if __name__ == '__main__':
    app = 0

    app = QApplication(sys.argv)
    circle_fit_widget = CircleFitWidget()

    # Create a demo transfer function
    w = np.linspace(0, 25, 3e2)
    a = func(w, 10, 1e-2, 8e12) + func(w, 5, 1e-1, 8e12) + func(w, 20, 5e-2, 8e12) + func(w, 12, 2e-2, 8e12) + 5e10*np.random.normal(size=w.size)

    circle_fit_widget.set_data(w, a)
    plt.figure()

    sys.exit(app.exec_())

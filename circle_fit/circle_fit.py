from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout

import numpy as np
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
from scipy.optimize import curve_fit, fmin
import matplotlib.pyplot as plt

import sys


pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('antialias', True)
defaultpen = pg.mkPen('k')


# External functions ----------------------------------------------------------
def to_dB(x):
    """A simple function that converts x to dB"""
    return 20*np.log10(x)


def from_dB(x):
    """A simple function that converts x in dB to a ratio over 1"""
    return 10**(x/20)


def sdof_modal_peak(w, wr, zr, cr, phi):
    """A modal peak"""
    return cr*np.exp(phi) / (wr**2 - w**2 + 2j * zr * wr**2)


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
    x = x0 + R0[0]*np.cos(theta)
    y = y0 + R0[0]*np.sin(theta)
    return x, y


# Circle Fit window -----------------------------------------------------------
class CircleFitWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()

        self.init_ui()

    # Initialisation functions ------------------------------------------------
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
        # Region of interest selector
        self.init_roi()
        self.region_select_plot.addItem(self.roi)

        self.roi.sigRegionChanged.connect(self.update_zoom)
        self.roi.sigRegionChanged.connect(self.update_plots)
        self.transfer_func_plot.sigXRangeChanged.connect(self.update_roi)
        self.transfer_func_plot.sigXRangeChanged.connect(self.update_plots)

        # # Circle plot
        self.circle_plot_w = pg.PlotWidget(title="Circle fit",
                                           labels={'bottom': ("Re"),
                                                   'left': ("Im")})
        self.circle_plot = self.circle_plot_w.getPlotItem()
        #self.circle_plot.setMouseEnabled(x=False, y=False)
        self.circle_plot.setAspectLocked(lock=True, ratio=1)
        self.circle_plot.showGrid(x=True, y=True)

        # # Layout
        plots = QGridLayout()
        plots.addWidget(self.transfer_func_plot_w, 0, 0)
        plots.addWidget(self.region_select_plot_w, 0, 1)
        plots.addWidget(self.circle_plot_w, 2, 1)
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


    def set_data(self, w=None, a=None):
        if a is not None:
            self.a = a
        if w is not None:
            self.w = w
        else:
            pass
        self.transfer_func_plot.plot(x=self.w, y=to_dB(np.abs(self.a)), pen=defaultpen)
        self.region_select_plot.plot(x=self.w, y=to_dB(np.abs(self.a)), pen=defaultpen)
        self.update_plots()

    # Update functions --------------------------------------------------------
    def update_zoom(self):
        self.w_min, self.a_min = self.roi.pos()
        self.w_max, self.a_max = self.roi.pos() + self.roi.size()
        self.transfer_func_plot.setXRange(self.w_min, self.w_max, padding=0)
        self.transfer_func_plot.setYRange(self.a_min, self.a_max, padding=0)

    def update_roi(self):
        region = np.asarray(self.transfer_func_plot.getViewBox().viewRange())
        self.roi.setPos(region[:, 0])
        self.roi.setSize(region[:, 1] - region[:, 0])

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

    def update_plots(self):
        # Get zoomed in region
        self.get_viewed_region()

        # Clear the current plots
        self.circle_plot.clear()
        self.transfer_func_plot.clear()
        # Delete the old legend and make a new one
        #self.circle_plot.getViewBox().removeItem(self.circle_plot.legend)
        #self.circle_plot.addLegend()

        # Plot the raw data
        self.circle_plot.plot(self.a_reg.real, self.a_reg.imag, pen=None,
                              symbol='o', symbolPen=None, symbolBrush='r',
                              name="Data")
        self.transfer_func_plot.plot(w, np.abs(to_dB(self.a)), pen=defaultpen)

        # Plot the circle (geometric fit)
        # Recalculate circle
        self.x0, self.y0, self.R0 = circle_fit(self.a_reg)
        self.x_c, self.y_c = plot_circle(self.x0, self.y0, self.R0)

        self.circle_plot.plot(self.x_c, self.y_c,
                              pen=pg.mkPen('k', width=2, style=QtCore.Qt.DashLine))

        # Plot the circle we're using to get the values
        w_circle = np.linspace(0, self.w.max(), 1e5)
        wr, zr, cr, phi = self.sdof_get_parameters()
        print("wr={}, zr={}, cr={}, ph={}".format(wr, zr, cr, phi))
        self.reg_peak = sdof_modal_peak(w_circle, wr, zr, cr, phi)
        self.circle_plot.plot(self.reg_peak.real, self.reg_peak.imag, pen=pg.mkPen('m', width=1.5),
                              name="Jim's method")
        self.transfer_func_plot.plot(w_circle, np.abs(to_dB(self.reg_peak)), pen='m')

    def sdof_modal_peak_optimisation_function(self, w, phi, wr, zr, cr):
        f = self.x0 + 1j*self.y0 - self.R0 * np.exp(1j*phi) \
            - sdof_modal_peak(w, wr, zr, cr, phi)
        return np.real(f * f.conjugate())

    def sdof_get_parameters(self):
        # # Find initial parameters for curve fitting
        # Find where the peak is - the maximum magnitude of the amplitude
        # within the region
        i = np.where(np.abs(self.a_reg) == np.abs(self.a_reg).max())[0][0]
        # Take the frequency at the max amplitude as a
        # first resonant frequency guess
        wr0 = self.w_reg[i]
        # Take the max amplitude as a first guess for the modal constant
        cr0 = np.abs(self.a_reg[i])
        phi0 = np.angle(self.a_reg[i])
        # First guess of damping factor of 1% (Q of 100)
        zr0 = 0.01

        # # Find the parameter values that give a minimum of
        # the optimisation function
        popts, pconv = curve_fit(self.sdof_modal_peak_optimisation_function,
                                 self.w_reg,
                                 np.real(self.a_reg * self.a_reg.conjugate()),
                                 [phi0, wr0, zr0, cr0])

        phi = popts[0]
        wr = popts[1]
        zr = popts[2]
        cr = popts[3]

        return wr, zr, cr, phi

if __name__ == '__main__':
    app = 0

    app = QApplication(sys.argv)
    circle_fit_widget = CircleFitWidget()

    # Create a demo transfer function
    w = np.linspace(0, 25, 3e2)
    a = sdof_modal_peak(w, 10, 0.008, 8e12, 0) \
        + sdof_modal_peak(w, 5, 0.006, 8e12, 0) \
        + sdof_modal_peak(w, 20, 0.01, 8e12, 0) \
        + sdof_modal_peak(w, 12, 0.003, -8e12, 0) \
        #+ 5e10*np.random.normal(size=w.size)

    circle_fit_widget.set_data(w, a)

    sys.exit(app.exec_())

import numpy as np
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
# pg.setConfigOption('antialias', True)
defaultpen = pg.mkPen('k')


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
    x = x0 + R0[0]*np.cos(theta)
    y = y0 + R0[0]*np.sin(theta)
    #x = x0[0] + R0[0]*np.cos(theta)
    #y = y0[0] + R0[0]*np.sin(theta)
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

        # # Circle plot
        self.circle_plot_w = pg.PlotWidget(title="Circle fit",
                                           labels={'bottom': ("Re"),
                                                   'left': ("Im")})
        self.circle_plot = self.circle_plot_w.getPlotItem()
        self.circle_plot.setMouseEnabled(x=False, y=False)
        self.circle_plot.setAspectLocked(lock=True, ratio=1)

        # # Fit plot

        self.fit_plot_w = pg.PlotWidget(title="Fitted peak",
                                        labels={'bottom': ("Frequency", "rad"),
                                                'left': ("Transfer Function", "dB")})
        self.fit_plot = self.fit_plot_w.getPlotItem()
        self.fit_plot.setMouseEnabled(x=False, y=False)
        # # Layout
        plots = QGridLayout()
        plots.addWidget(self.transfer_func_plot_w, 0, 0)
        plots.addWidget(self.region_select_plot_w, 0, 1)
        plots.addWidget(self.circle_plot_w, 2, 1)
        plots.addWidget(self.fit_plot_w, 2, 0)
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
        self.fit_plot.setXRange(self.w_min, self.w_max, padding=0)
        self.fit_plot.setYRange(self.a_min, self.a_max, padding=0)

    def update_roi(self):
        region = np.asarray(self.transfer_func_plot.getViewBox().viewRange())
        self.roi.setPos(region[:, 0])
        self.roi.setSize(region[:, 1] - region[:, 0])

    def update_plots(self):
        # Get zoomed in region
        self.get_viewed_region()

        """ TEMA METHOD: """
        w_circle = np.linspace(0, self.w.max(), 1e5)
        self.circle_plot.clear()
        self.circle_plot.getViewBox().removeItem(self.circle_plot.legend)
        self.circle_plot.addLegend()
        # Recalculate circle
        self.x0, self.y0, self.R0 = circle_fit(self.a_reg)
        self.x_c, self.y_c = plot_circle(self.x0, self.y0, self.R0)
        wr, zr, c = self.find_vals()
        self.f = func(w_circle, wr, zr, c)
        self.circle_plot.plot(self.f.real, self.f.imag, pen='g',
                              name="TEMA method")

        # Update plot
        # Plot the data
        self.x_c, self.y_c = plot_circle(0, -np.sqrt(self.y0**2 + self.x0**2), self.R0)
        self.circle_plot.plot(self.a_reg.real, self.a_reg.imag, pen=None,
                              symbol='o', symbolPen=None, symbolBrush='r',
                              name="Data")
        # Plot the circle
        self.circle_plot.plot(self.x_c, self.y_c,
                              pen=pg.mkPen('k', width=2, style=QtCore.Qt.DashLine))

        """ ITERATIVE METHOD: """
        wr, zr, c = self.fit_peak()
        self.f = func(w_circle, wr, zr, c)
        self.circle_plot.plot(self.f.real, self.f.imag, pen='b',
                              name="Iterative method")
        self.fit_plot.clear()
        self.fit_plot.plot(w, np.abs(to_dB(self.a)), pen=defaultpen)
        self.fit_plot.plot(w_circle, np.abs(to_dB(func(w_circle, wr, zr, c))), pen='b')
        wr, zr, c = self.find_vals()
        self.fit_plot.plot(w_circle, np.abs(to_dB(func(w_circle, wr, zr, c))), pen='g')

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
        self.transfer_func_plot.plot(x=self.w, y=to_dB(np.abs(self.a)), pen=defaultpen)
        self.region_select_plot.plot(x=self.w, y=to_dB(np.abs(self.a)), pen=defaultpen)
        self.update_plots()

    def find_vals(self):
        self.get_viewed_region()
        self.a_reg_abs = np.abs(self.a_reg)

        # First guess of resonant frequency - the peak
        i = np.where(self.a_reg_abs == np.abs(self.a_reg.max()))[0][0]

        ## Resonant frequency and phase angle
        # Four initial data points
        w0, w1, w2, w3 = self.w_reg[i-2], self.w_reg[i-1], self.w_reg[i+1], self.w_reg[i+2]
        t0, t1, t2, t3 = np.angle(self.a_reg[i-2]), np.angle(self.a_reg[i-1]), np.angle(self.a_reg[i+1]), np.angle(self.a_reg[i+2])

        t0t1 = self.tAtB(t0, t1, w0, w1)
        t0t1t2 = self.tAtBtC(t0, t1, t2, w0, w1, w2)
        t0t1t2t3 = self.tAtBtCtD(t0, t1, t2, t3, w0, w1, w2, w3)

        wr2 = (w0**2 + w1**2 + w2**2 - (t0t1t2 / t0t1t2t3)) / 3
        wr = np.sqrt(wr2)
        tr = t0 + (wr2 - w0**2)*t0t1 + (wr2 - w0**2)*(wr2 - w1**2)*t0t1t2 + (wr2 - w0**2)*(wr2 - w1**2)*(wr2 - w2**2)*t0t1t2t3

        ## Damping factor
        w1, w2, w3, w4, w5, w6 = self.w_reg[i-3], self.w_reg[i-2], self.w_reg[i-1], self.w_reg[i+1], self.w_reg[i+2], self.w_reg[i+3]
        t1, t2, t3, t4, t5, t6 = np.angle(self.a_reg[i-3]), np.angle(self.a_reg[i-2]), np.angle(self.a_reg[i-1]), np.angle(self.a_reg[i+1]), np.angle(self.a_reg[i+2]), np.angle(self.a_reg[i+3])

        # Take mean of points
        #3,4
        zr34 = self.calc_zr(wr, tr, w3, w4, t3, t4)

        #2,5
        zr25 = self.calc_zr(wr, tr, w2, w5, t2, t5)

        #1,6
        zr16 = self.calc_zr(wr, tr, w1, w6, t1, t6)

        zr = (zr34 + zr25 + zr16)/3

        ## Modal Constant
        # Modulus:
        C = 2*self.R0*wr2*2*zr

        # Phase angle
        xD = 0
        yD = 0
        phi = np.arctan((self.x0 - xD) / (self.y0 - yD))

        return wr, zr, C#*np.exp(1j*phi)

    def tAtB(self, tA, tB, wA, wB):
        return (tA - tB) / (wA**2 - wB**2)

    def tAtBtC(self, tA, tB, tC, wA, wB, wC):
        return (self.tAtB(tA, tB, wA, wB) - self.tAtB(tB, tC, wB, wC)) / (wA**2 - wC**2)

    def tAtBtCtD(self, tA, tB, tC, tD, wA, wB, wC, wD):
        return (self.tAtBtC(tA, tB, tC, wA, wB, wC) - self.tAtBtC(tB, tC, tD, wB, wC, wD)) / (wA**2 - wD**2)

    def calc_zr(self, wr, tr, wb, wa, tb, ta):
        return ((wa**2 - wb**2)/ (wr**2 * (np.tan(ta - tr) + np.tan(tr - tb))))/2

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
    a = func(w, 10, 1e-2, 8e12) + func(w, 5, 1e-1, 8e12) + func(w, 20, 5e-2, 8e12) + func(w, 12, 2e-2, 8e12) #+ 5e10*np.random.normal(size=w.size)

    circle_fit_widget.set_data(w, a)

    sys.exit(app.exec_())

from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QTableWidget,
                             QDoubleSpinBox, QCheckBox, QPushButton, QGroupBox,
                             QVBoxLayout, QHBoxLayout)

import numpy as np
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
from scipy.optimize import curve_fit

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
                                                  labels={'bottom':
                                                          ("Frequency", "rad"),
                                                          'left':
                                                          ("Transfer Function",
                                                           "dB")})
        self.transfer_func_plot = self.transfer_func_plot_w.getPlotItem()

        # # Region Selection plot
        self.region_select_plot_w = pg.PlotWidget(title="Region Selection",
                                                  labels={'bottom':
                                                          ("Frequency", "rad"),
                                                          'left':
                                                          ("Transfer Function",
                                                           "dB")})
        self.region_select_plot = self.region_select_plot_w.getPlotItem()
        self.region_select_plot.setMouseEnabled(x=False, y=False)

        self.region_select = pg.LinearRegionItem()
        self.region_select.setZValue(-10)
        self.region_select_plot.addItem(self.region_select)

        self.region_select.sigRegionChanged.connect(self.update_zoom)
        self.region_select.sigRegionChanged.connect(self.update_plots)
        self.transfer_func_plot.sigXRangeChanged.connect(self.update_region)
        self.transfer_func_plot.sigXRangeChanged.connect(self.update_plots)

        # # Circle plot
        self.circle_plot_w = pg.PlotWidget(title="Circle fit",
                                           labels={'bottom': ("Re"),
                                                   'left': ("Im")})
        self.circle_plot = self.circle_plot_w.getPlotItem()
        # self.circle_plot.setMouseEnabled(x=False, y=False)
        self.circle_plot.setAspectLocked(lock=True, ratio=1)
        self.circle_plot.showGrid(x=True, y=True)

        # # Table of results
        self.init_table()

        # # Additional controls
        self.add_peak_btn = QPushButton(self)
        self.add_peak_btn.setText("Add new peak")
        self.add_peak_btn.clicked.connect(self.add_sdof_row)

        self.delete_selected_btn = QPushButton(self)
        self.delete_selected_btn.setText("Delete selected")
        self.delete_selected_btn.clicked.connect(self.delete_selected)

        controls = QGridLayout()
        spacer_hbox = QHBoxLayout()
        spacer_hbox.addStretch(1)
        controls.addWidget(self.delete_selected_btn, 0, 0)
        controls.addLayout(spacer_hbox, 0, 1)
        controls.addWidget(self.add_peak_btn, 0, 2)

        self.groupbox = QGroupBox(self)
        self.groupbox.setTitle("Results")

        self.groupbox_vbox = QVBoxLayout()
        self.groupbox_vbox.addWidget(self.tableWidget)
        self.groupbox_vbox.addLayout(controls)

        self.groupbox.setLayout(self.groupbox_vbox)

        # # Layout
        layout = QGridLayout()
        layout.addWidget(self.transfer_func_plot_w, 0, 0)
        layout.addWidget(self.region_select_plot_w, 0, 1)
        layout.addWidget(self.groupbox, 2, 0)
        layout.addWidget(self.circle_plot_w, 2, 1)
        self.setLayout(layout)

        self.setWindowTitle('Circle fit')
        self.show()

    def init_table(self):
        self.tableWidget = QTableWidget(self)

        self.tableWidget.setColumnCount(6)
        self.tableWidget.setHorizontalHeaderLabels(["", "Frequency (rad)",
                                                    "Damping ratio",
                                                    "Amplitude (dB)", "Phase (rad)", ""])
        header = self.tableWidget.horizontalHeader()
        header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(1, QtGui.QHeaderView.Stretch)
        header.setResizeMode(2, QtGui.QHeaderView.Stretch)
        header.setResizeMode(3, QtGui.QHeaderView.Stretch)
        header.setResizeMode(4, QtGui.QHeaderView.Stretch)
        header.setResizeMode(5, QtGui.QHeaderView.ResizeToContents)

        self.row_list = []
        self.modal_peaks = []

        self.add_sdof_row()

    # Interaction functions ---------------------------------------------------
    def add_sdof_row(self):
        # Add the new row at the end
        self.tableWidget.insertRow(self.tableWidget.rowCount())
        # Go to the new row
        self.tableWidget.setCurrentCell(self.tableWidget.rowCount()-1, 0)

        # Create a new dict in the list of rows to store the
        # widgets for this row in
        self.row_list.append({})

        # Create a new dict in the list of modal peaks to store the
        # values for this peak in
        self.modal_peaks.append({})

        # Create the plot item for this peak
        self.modal_peaks[-1]["plot1"] = pg.PlotDataItem()
        self.modal_peaks[-1]["plot2"] = pg.PlotDataItem()
        self.transfer_func_plot.addItem(self.modal_peaks[-1]["plot1"])
        self.region_select_plot.addItem(self.modal_peaks[-1]["plot2"])

        # Create a load of widgets to fill the row - store them in the new dict
        self.row_list[-1]["selectbox"] = QCheckBox()
        self.row_list[-1]["selectbox"].stateChanged.connect(self.select_peak)
        self.row_list[-1]["selectbox"].stateChanged.connect(self.set_active_row)
        self.row_list[-1]["freqbox"] = QDoubleSpinBox()
        self.row_list[-1]["freqbox"].valueChanged.connect(self.update_plots)
        self.row_list[-1]["freqbox"].valueChanged.connect(self.set_active_row)
        self.row_list[-1]["freqbox"].setSingleStep(0.01)
        self.row_list[-1]["freqbox"].setRange(0, 4096*2*np.pi)
        self.row_list[-1]["zbox"] = QDoubleSpinBox()
        self.row_list[-1]["zbox"].valueChanged.connect(self.update_plots)
        self.row_list[-1]["zbox"].valueChanged.connect(self.set_active_row)
        self.row_list[-1]["zbox"].setSingleStep(0.0001)
        self.row_list[-1]["zbox"].setRange(0, 10)
        self.row_list[-1]["zbox"].setDecimals(4)
        self.row_list[-1]["ampbox"] = QDoubleSpinBox()
        self.row_list[-1]["ampbox"].valueChanged.connect(self.update_plots)
        self.row_list[-1]["ampbox"].valueChanged.connect(self.set_active_row)
        self.row_list[-1]["ampbox"].setSingleStep(0.1)
        self.row_list[-1]["ampbox"].setRange(0, 1e3)
        self.row_list[-1]["phasebox"] = QDoubleSpinBox()
        self.row_list[-1]["phasebox"].valueChanged.connect(self.update_plots)
        self.row_list[-1]["phasebox"].valueChanged.connect(self.set_active_row)
        self.row_list[-1]["phasebox"].setSingleStep(0.01)
        self.row_list[-1]["phasebox"].setRange(-np.pi, np.pi)
        self.row_list[-1]["lockbtn"] = QPushButton()
        self.row_list[-1]["lockbtn"].setText("Lock")
        self.row_list[-1]["lockbtn"].setCheckable(True)
        self.row_list[-1]["lockbtn"].clicked[bool].connect(self.lock_peak)
        self.row_list[-1]["lockbtn"].clicked.connect(self.set_active_row)


        # Fill the row with widgets
        self.tableWidget.setCellWidget(self.tableWidget.rowCount() - 1, 0,
                                       self.row_list[-1]["selectbox"])
        self.tableWidget.setCellWidget(self.tableWidget.rowCount() - 1, 1,
                                       self.row_list[-1]["freqbox"])
        self.tableWidget.setCellWidget(self.tableWidget.rowCount() - 1, 2,
                                       self.row_list[-1]["zbox"])
        self.tableWidget.setCellWidget(self.tableWidget.rowCount() - 1, 3,
                                       self.row_list[-1]["ampbox"])
        self.tableWidget.setCellWidget(self.tableWidget.rowCount() - 1, 4,
                                       self.row_list[-1]["phasebox"])
        self.tableWidget.setCellWidget(self.tableWidget.rowCount() - 1, 5,
                                       self.row_list[-1]["lockbtn"])

    def select_peak(self):
        pass

    def lock_peak(self, clicked):
        pass

    def delete_selected(self):
        pass

    def set_active_row(self):
        for i, row in enumerate(self.row_list):
            if self.sender() in row.values():
                self.tableWidget.setCurrentCell(i, 0)

    def set_data(self, w=None, a=None):
        if a is not None:
            self.a = a
        if w is not None:
            self.w = w
        else:
            pass
        # Plot the transfer function
        self.transfer_function1 = pg.PlotDataItem(x=self.w, y=to_dB(np.abs(self.a)),
                                     pen=defaultpen)
        self.transfer_func_plot.addItem(self.transfer_function1)
        self.transfer_function2 = pg.PlotDataItem(x=self.w, y=to_dB(np.abs(self.a)),
                                     pen=defaultpen)
        self.region_select_plot.addItem(self.transfer_function2)

        self.transfer_func_plot.autoRange()
        self.transfer_func_plot.disableAutoRange()

        self.region_select_plot.autoRange()
        self.region_select_plot.disableAutoRange()

        # Create the plot items for the modal peak fit
        self.circle_plot_modal_peak = pg.PlotDataItem()
        self.circle_plot.addItem(self.circle_plot_modal_peak)

        # Create the plot items for the data points
        self.circle_plot_points = pg.PlotDataItem()
        self.circle_plot.addItem(self.circle_plot_points)

        self.update_plots()

    # Update functions --------------------------------------------------------
    def update_zoom(self):
        self.transfer_func_plot.setXRange(*self.region_select.getRegion(),
                                          padding=0)

    def update_region(self):
        self.region_select.setRegion(self.transfer_func_plot.getViewBox().viewRange()[0])

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

    def update_plots(self, value=None):
        self.region_select.setBounds((self.w.min(), self.w.max()))
        # Get zoomed in region
        self.get_viewed_region()

        # If the current peak is not locked
        if not self.row_list[self.tableWidget.currentRow()]["lockbtn"].isChecked():
            # Recalculate the geometric circle fit
            self.x0, self.y0, self.R0 = circle_fit(self.a_reg)
            self.w_circle = np.linspace(0, self.w.max(), 1e5)

            if self.sender() == self.transfer_func_plot or self.sender() == self.region_select:
                self.update_plot_from_plot()
                # Update what is displayed in the table
                self.update_row_from_plot()
            else:
                self.update_plot_from_row(value)

            # Plot the raw data
            self.circle_plot_points.setData(self.a_reg.real, self.a_reg.imag, pen=None,
                                  symbol='o', symbolPen=None, symbolBrush='k',
                                  symbolSize=6)


            # Recalculate the fitted modal peak
            self.modal_peaks[self.tableWidget.currentRow()]["data"] = sdof_modal_peak(self.w_circle,
                                                           self.modal_peaks[self.tableWidget.currentRow()]["wr"],
                                                           self.modal_peaks[self.tableWidget.currentRow()]["zr"],
                                                           self.modal_peaks[self.tableWidget.currentRow()]["cr"],
                                                           self.modal_peaks[self.tableWidget.currentRow()]["phi"])

            # Plot the fitted modal peak
            self.circle_plot_modal_peak.setData(self.modal_peaks[self.tableWidget.currentRow()]["data"].real + self.x0,
                                                self.modal_peaks[self.tableWidget.currentRow()]["data"].imag,
                                                pen=pg.mkPen('m', width=1.5))

            self.modal_peaks[self.tableWidget.currentRow()]["plot1"].setData(self.w_circle,
                                                       np.abs(to_dB(self.modal_peaks[self.tableWidget.currentRow()]["data"])),
                                                       pen='m')
            self.modal_peaks[self.tableWidget.currentRow()]["plot2"].setData(self.w_circle,
                                                       np.abs(to_dB(self.modal_peaks[self.tableWidget.currentRow()]["data"])),
                                                       pen='m')


    def update_row_from_plot(self):
        self.row_list[self.tableWidget.currentRow()]["freqbox"].setValue(self.modal_peaks[self.tableWidget.currentRow()]["wr"])
        self.row_list[self.tableWidget.currentRow()]["zbox"].setValue(self.modal_peaks[self.tableWidget.currentRow()]["zr"])
        self.row_list[self.tableWidget.currentRow()]["ampbox"].setValue(to_dB(self.modal_peaks[self.tableWidget.currentRow()]["cr"]))
        self.row_list[self.tableWidget.currentRow()]["phasebox"].setValue(self.modal_peaks[self.tableWidget.currentRow()]["phi"])

    def update_plot_from_row(self, value):
        if self.sender() == self.row_list[self.tableWidget.currentRow()]["freqbox"]:
            self.modal_peaks[self.tableWidget.currentRow()]["wr"] = value
        if self.sender() == self.row_list[self.tableWidget.currentRow()]["zbox"]:
            self.modal_peaks[self.tableWidget.currentRow()]["zr"] = value
        if self.sender() == self.row_list[self.tableWidget.currentRow()]["ampbox"]:
            self.modal_peaks[self.tableWidget.currentRow()]["cr"] = from_dB(value)
        if self.sender() == self.row_list[self.tableWidget.currentRow()]["phasebox"]:
            self.modal_peaks[self.tableWidget.currentRow()]["phi"] = value

    def update_plot_from_plot(self):
        # Fit a modal peak circle to the geometric circle
        self.modal_peaks[self.tableWidget.currentRow()]["wr"], \
         self.modal_peaks[self.tableWidget.currentRow()]["zr"], \
         self.modal_peaks[self.tableWidget.currentRow()]["cr"], \
         self.modal_peaks[self.tableWidget.currentRow()]["phi"] = self.sdof_get_parameters()

# Fitting functions -----------------------------------------------------------
    def sdof_modal_peak_optimisation_function(self, w, phi, wr, zr, cr):
        f = self.x0 + 1j*self.y0 - self.R0 * np.exp(1j*(phi - np.pi/2)) \
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

        return wr, zr, np.abs(cr), phi


if __name__ == '__main__':
    app = 0

    app = QApplication(sys.argv)
    c = CircleFitWidget()

    # Create a demo transfer function
    w = np.linspace(0, 25, 3e2)
    a = sdof_modal_peak(w, 5, 0.006, 8e12, 0) \
        + sdof_modal_peak(w, 10, 0.008, 8e12, np.pi/2) \
        + sdof_modal_peak(w, 12, 0.003, -8e12, 0) \
        + sdof_modal_peak(w, 20, 0.01, 22e12, 0) \
        # + 5e10*np.random.normal(size=w.size)

    c.set_data(w, a)

    sys.exit(app.exec_())

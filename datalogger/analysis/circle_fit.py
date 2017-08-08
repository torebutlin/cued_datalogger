import sys
sys.path.append('../')
sys.path.append('../acquisition')

from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QTableWidget,
                             QDoubleSpinBox, QCheckBox, QPushButton, QGroupBox,
                             QVBoxLayout, QHBoxLayout, QLabel, QComboBox)

import numpy as np
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
from scipy.optimize import curve_fit

from channel import ChannelSet
from matlab_import import import_from_mat

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
    return cr*np.exp(1j*phi) / (wr**2 - w**2 + 2j * zr * wr**2)


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

        self.w = np.zeros(1)


        self.init_ui()

    # Initialisation functions ------------------------------------------------
    def init_ui(self):
        # # Transfer function plotlock
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

        self.region_select.sigRegionChangeFinished.connect(self.autorange_to_region)
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

        # # Create the items for the plots
        self.transfer_function1 = pg.PlotDataItem(pen=defaultpen)
        self.transfer_func_plot.addItem(self.transfer_function1)

        self.transfer_function2 = pg.PlotDataItem(pen=defaultpen)
        self.region_select_plot.addItem(self.transfer_function2)

        self.constructed_transfer_fn1 = pg.PlotDataItem(pen='b')
        self.transfer_func_plot.addItem(self.constructed_transfer_fn1)

        self.constructed_transfer_fn2 = pg.PlotDataItem(pen='b')
        self.region_select_plot.addItem(self.constructed_transfer_fn2)

        self.circle_plot_points = pg.PlotDataItem()
        self.circle_plot.addItem(self.circle_plot_points)

        self.circle_plot_modal_peak = pg.PlotDataItem()
        self.circle_plot.addItem(self.circle_plot_modal_peak)

        # # Additional controls
        self.add_peak_btn = QPushButton(self)
        self.add_peak_btn.setText("Add new peak")
        self.add_peak_btn.clicked.connect(self.add_peak)

        self.delete_selected_btn = QPushButton(self)
        self.delete_selected_btn.setText("Delete selected")
        self.delete_selected_btn.clicked.connect(self.delete_selected)

        controls = QGridLayout()
        spacer_hbox = QHBoxLayout()
        spacer_hbox.addStretch(1)
        controls.addWidget(self.delete_selected_btn, 0, 0)
        controls.addLayout(spacer_hbox, 0, 1)
        controls.addWidget(self.add_peak_btn, 0, 2)

        # # Transfer function reconstruction
        self.construct_transfer_fn_btn = QPushButton(self)
        self.construct_transfer_fn_btn.setText("Construct transfer function")
        self.construct_transfer_fn_btn.clicked.connect(self.construct_transfer_fn)

        self.show_transfer_fn_checkbox = QCheckBox(self)
        self.show_transfer_fn_checkbox.setText("Show/hide")
        self.show_transfer_fn_checkbox.stateChanged.connect(self.show_transfer_fn)

        transfer_fn_hbox = QHBoxLayout()
        transfer_fn_hbox.addWidget(self.construct_transfer_fn_btn)
        transfer_fn_hbox.addWidget(self.show_transfer_fn_checkbox)
        transfer_fn_hbox.addLayout(spacer_hbox)

        transfer_fn_groupbox = QGroupBox(self)
        transfer_fn_groupbox.setTitle("Transfer function")
        transfer_fn_groupbox.setLayout(transfer_fn_hbox)

        # # Table of results
        self.init_table()

        results_groupbox = QGroupBox(self)
        results_groupbox.setTitle("Results")

        results_groupbox_vbox = QVBoxLayout()
        results_groupbox_vbox.addWidget(self.tableWidget)
        results_groupbox_vbox.addLayout(controls)

        results_groupbox.setLayout(results_groupbox_vbox)

        # # Fit controls
        self.init_fit_controls()

        # # Region selection controls
        self.autorange_to_region_checkbox = QCheckBox("Autorange to region")
        self.autorange_to_region_checkbox.clicked.connect(self.autorange_to_region)

        selection_vbox_spacer = QVBoxLayout()
        selection_vbox_spacer.addStretch(1)

        selection_vbox = QVBoxLayout()
        selection_vbox.addWidget(self.autorange_to_region_checkbox)
        selection_vbox.addLayout(selection_vbox_spacer)

        selection_groupbox = QGroupBox()
        selection_groupbox.setTitle("Selection controls")
        selection_groupbox.setLayout(selection_vbox)

        # # Widget layout
        controls_hbox = QHBoxLayout()
        controls_hbox.addWidget(self.fit_controls_groupbox)
        controls_hbox.addWidget(selection_groupbox)

        controls_vbox = QVBoxLayout()
        controls_vbox.addWidget(results_groupbox)
        controls_vbox.addWidget(transfer_fn_groupbox)
        controls_vbox.addLayout(controls_hbox)

        layout = QGridLayout()
        layout.addWidget(self.transfer_func_plot_w, 0, 0)
        layout.addWidget(self.region_select_plot_w, 0, 1)
        layout.addLayout(controls_vbox, 2, 0)
        layout.addWidget(self.circle_plot_w, 2, 1)
        self.setLayout(layout)

        self.setWindowTitle('Circle fit')
        self.show()

    def init_table(self):
        self.tableWidget = QTableWidget(self)

        self.tableWidget.setColumnCount(6)
        self.tableWidget.setHorizontalHeaderLabels(["", "Frequency (rad)",
                                                    "Damping ratio",
                                                    "Amplitude", "Phase (rad)",
                                                    "\N{LOCK}"])
        header = self.tableWidget.horizontalHeader()
        header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(1, QtGui.QHeaderView.Stretch)
        header.setResizeMode(2, QtGui.QHeaderView.Stretch)
        header.setResizeMode(3, QtGui.QHeaderView.Stretch)
        header.setResizeMode(4, QtGui.QHeaderView.Stretch)
        header.setResizeMode(5, QtGui.QHeaderView.ResizeToContents)

        self.row_list = []
        self.modal_peaks = []

    def init_fit_controls(self):
        self.fit_controls_freq_combobox = QComboBox()
        self.fit_controls_z_combobox = QComboBox()
        self.fit_controls_amp_combobox = QComboBox()
        self.fit_controls_phase_combobox = QComboBox()

        self.fit_controls_freq_combobox.addItems(["Automatic", "Manual"])
        self.fit_controls_z_combobox.addItems(["Automatic", "Manual"])
        self.fit_controls_amp_combobox.addItems(["Automatic", "Manual"])
        self.fit_controls_phase_combobox.addItems(["Automatic", "Manual"])

        self.fit_controls_freq_combobox.setCurrentIndex(0)
        self.fit_controls_z_combobox.setCurrentIndex(0)
        self.fit_controls_amp_combobox.setCurrentIndex(0)
        self.fit_controls_phase_combobox.setCurrentIndex(0)

        self.fit_controls_reset_btn = QPushButton("Reset")
        self.fit_controls_reset_btn.clicked.connect(self.reset_to_auto_fit)

        fit_controls_grid_layout = QGridLayout()
        fit_controls_grid_layout.addWidget(QLabel("Parameters"), 0, 0)
        fit_controls_grid_layout.addWidget(QLabel("Frequency:"), 1, 0)
        fit_controls_grid_layout.addWidget(self.fit_controls_freq_combobox, 1, 1)
        fit_controls_grid_layout.addWidget(QLabel("Damping ratio:"), 2, 0)
        fit_controls_grid_layout.addWidget(self.fit_controls_z_combobox, 2, 1)
        fit_controls_grid_layout.addWidget(QLabel("Amplitude:"), 3, 0)
        fit_controls_grid_layout.addWidget(self.fit_controls_amp_combobox, 3, 1)
        fit_controls_grid_layout.addWidget(QLabel("Phase:"), 4, 0)
        fit_controls_grid_layout.addWidget(self.fit_controls_phase_combobox, 4, 1)
        fit_controls_grid_layout.addWidget(self.fit_controls_reset_btn, 5, 1)

        fit_controls_grid_layout.setColumnStretch(2, 1)

        self.fit_controls_groupbox = QGroupBox()
        self.fit_controls_groupbox.setTitle("Fit controls")
        self.fit_controls_groupbox.setLayout(fit_controls_grid_layout)

    # Interaction functions ---------------------------------------------------
    def reset_to_auto_fit(self):
        self.fit_controls_freq_combobox.setCurrentIndex(0)
        self.fit_controls_z_combobox.setCurrentIndex(0)
        self.fit_controls_amp_combobox.setCurrentIndex(0)
        self.fit_controls_phase_combobox.setCurrentIndex(0)


    def add_peak(self):
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
        self.row_list[-1]["selectbox"].toggle()
        self.row_list[-1]["selectbox"].stateChanged.connect(self.update_peak_selection)
        self.row_list[-1]["freqbox"] = QDoubleSpinBox()
        self.row_list[-1]["freqbox"].valueChanged.connect(self.update_plots)
        self.row_list[-1]["freqbox"].setSingleStep(0.01)
        self.row_list[-1]["freqbox"].setRange(-9e99, 9e99)
        self.row_list[-1]["zbox"] = QDoubleSpinBox()
        self.row_list[-1]["zbox"].valueChanged.connect(self.update_plots)
        #self.row_list[-1]["zbox"].valueChanged.connect(self.update_spinbox_step)
        self.row_list[-1]["zbox"].setSingleStep(0.0001)
        self.row_list[-1]["zbox"].setRange(-9e99, 9e99)
        self.row_list[-1]["zbox"].setDecimals(4)
        self.row_list[-1]["ampbox"] = QDoubleSpinBox()
        self.row_list[-1]["ampbox"].valueChanged.connect(self.update_plots)
        self.row_list[-1]["ampbox"].valueChanged.connect(self.update_spinbox_step)
        self.row_list[-1]["ampbox"].setRange(-9e99, 9e99)
        self.row_list[-1]["phasebox"] = QDoubleSpinBox()
        self.row_list[-1]["phasebox"].valueChanged.connect(self.update_plots)
        self.row_list[-1]["phasebox"].setSingleStep(0.01)
        self.row_list[-1]["phasebox"].setRange(-9e99, 9e99)
        self.row_list[-1]["lockbtn"] = QPushButton()
        self.row_list[-1]["lockbtn"].setText("<")
        self.row_list[-1]["lockbtn"].setCheckable(True)
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

        # With pyqtgraph's addItem, all the other items are set back to being visible
        # so need to undo this for those that are unchecked
        self.update_peak_selection()
        self.show_transfer_fn()

        self.set_active_row(new_row=True)
        self.update_plots()

    def show_transfer_fn(self):
        if self.show_transfer_fn_checkbox.isChecked():
            self.constructed_transfer_fn1.show()
            self.constructed_transfer_fn2.show()
        else:
            self.constructed_transfer_fn1.hide()
            self.constructed_transfer_fn2.hide()

    def update_spinbox_step(self, value):
        if np.abs(value) > 1:
            # Set the step to 1% of the current value
            self.sender().setSingleStep(0.01 * value)
        else:
            self.sender().setSingleStep(0.01)

    def update_peak_selection(self):
        #self.set_active_row()
        for i, row in enumerate(self.row_list):
            checked = row["selectbox"].isChecked()

            for item in self.transfer_func_plot.items:
                if item == self.modal_peaks[i]["plot1"]:
                    item.setVisible(checked)

            for item in self.region_select_plot.items:
                if item == self.modal_peaks[i]["plot2"]:
                    item.setVisible(checked)

    def delete_selected(self):
        for i, row in enumerate(self.row_list):
            if row["selectbox"].isChecked():
                # Delete from table
                del self.row_list[i]
                self.tableWidget.removeRow(i)
                # Delete from graphs
                self.transfer_func_plot.removeItem(self.modal_peaks[i]["plot1"])
                self.region_select_plot.removeItem(self.modal_peaks[i]["plot2"])
                del self.modal_peaks[i]
        # With pyqtgraph's removeItem, all the other items are set back to being visible
        # so need to undo this for those that are unchecked
        self.update_peak_selection()
        self.show_transfer_fn()

    def set_active_row(self, checked=False, new_row=False):
        for i, row in enumerate(self.row_list):
            # If this was the row that was clicked, or a new row is being added
            if not new_row and self.sender() in row.values():
                # Set this row as the current row
                self.tableWidget.setCurrentCell(i, 0)

                if checked:
                    row["lockbtn"].setText("\N{LOCK}")
                    for name, widget in row.items():
                        if name != "lockbtn" and name != "selectbox":
                            widget.setDisabled(True)
                else:
                    row["lockbtn"].setText("<")
                    for widget in row.values():
                            widget.setDisabled(False)

            elif new_row and row is self.row_list[-1]:
                row["lockbtn"].setText("<")
                for widget in row.values():
                    widget.setDisabled(False)

            else:
                row["lockbtn"].setText("\N{LOCK}")
                for name, widget in row.items():
                    if name != "lockbtn" and name != "selectbox":
                        widget.setDisabled(True)

        self.update_plots()

    def set_data(self, w=None, a=None):
        if a is not None:
            self.a = a
        if w is not None:
            self.w = w
            # Create a more precise version for plotting the fit
            self.w_fit = np.linspace(0, self.w.max(), self.w.size*10)
        else:
            pass

        # Plot the transfer function
        self.transfer_function1.setData(x=self.w,
                                        y=to_dB(np.abs(self.a)))

        self.transfer_function2.setData(x=self.w,
                                        y=to_dB(np.abs(self.a)))

        self.transfer_func_plot.autoRange()
        self.transfer_func_plot.setXRange(self.w.min(), self.w.max())
        self.transfer_func_plot.setLimits(xMin=self.w.min(), xMax=self.w.max())
        self.transfer_func_plot.disableAutoRange()

        self.transfer_func_plot.autoRange()
        self.region_select_plot.setXRange(self.w.min(), self.w.max())
        self.region_select_plot.setLimits(xMin=self.w.min(), xMax=self.w.max())
        self.region_select_plot.disableAutoRange()

        self.region_select.setBounds((self.w.min(), self.w.max()))
        self.add_peak()

    def construct_transfer_fn(self):
        self.show_transfer_fn_checkbox.setChecked(True)
        self.constructed_transfer_fn = np.zeros_like(self.modal_peaks[-1]["data"])
        for i, peak in enumerate(self.modal_peaks):
            if self.row_list[i]["selectbox"].isChecked():
                self.constructed_transfer_fn += peak["data"]

        self.constructed_transfer_fn1.setData(x=self.w_fit,
                                              y=to_dB(np.abs(self.constructed_transfer_fn)))
        self.constructed_transfer_fn2.setData(x=self.w_fit,
                                              y=to_dB(np.abs(self.constructed_transfer_fn)))

    # Update functions --------------------------------------------------------
    def update_zoom(self):
        self.transfer_func_plot.setXRange(*self.region_select.getRegion(),
                                          padding=0)

    def autorange_to_region(self, checked):
        if self.autorange_to_region_checkbox.isChecked():
            self.region_select_plot.setXRange(*self.region_select.getRegion(),
                                              padding=1)
        else:
            self.region_select_plot.setXRange(self.w.min(), self.w.max())

    def update_region(self):
        self.region_select.setRegion(self.transfer_func_plot.getViewBox().viewRange()[0])

    def get_viewed_region(self):
        # Get the axes limits
        w_axis_lower, w_axis_upper = self.transfer_func_plot.getAxis('bottom').range

        w_in_display = (self.w >= w_axis_lower) & (self.w <= w_axis_upper)

        self.w_reg = np.extract(w_in_display, self.w)
        self.a_reg = np.extract(w_in_display, self.a)

        # Do something similar for the more precise w_fit - but get the indices
        # rather than the values
        w_fit_in_display = (self.w_fit >= w_axis_lower) & (self.w_fit <= w_axis_upper)
        self.fit_lower = np.where(w_fit_in_display)[0][0]
        self.fit_upper = np.where(w_fit_in_display)[0][-1]

    def update_plots(self, value=None):
        # If the current peak is not locked
        if not self.row_list[self.tableWidget.currentRow()]["lockbtn"].isChecked():
            # Get zoomed in region
            self.get_viewed_region()

            # Update the values
            if self.sender() in self.row_list[self.tableWidget.currentRow()].values():
                self.update_from_row(value)
            else:
                self.update_from_plot()

            # Recalculate the fitted modal peak
            #self.modal_peaks[self.tableWidget.currentRow()]["data"] = sdof_modal_peak(self.w_fit,
            #self.modal_peaks[self.tableWidget.currentRow()]["data"] = self.fitted_single_pole(self.w_fit,
            self.modal_peaks[self.tableWidget.currentRow()]["data"] = self.fitted_double_pole(self.w_fit,
                                                                                      self.modal_peaks[self.tableWidget.currentRow()]["wr"],
                                                                                      self.modal_peaks[self.tableWidget.currentRow()]["zr"],
                                                                                      self.modal_peaks[self.tableWidget.currentRow()]["cr"],
                                                                                      self.modal_peaks[self.tableWidget.currentRow()]["phi"])

            # Plot the raw data
            self.circle_plot_points.setData(self.a_reg.real, self.a_reg.imag, pen=None,
                                  ymbol='o', symbolPen=None, symbolBrush='k',
                                  symbolSize=6)

            # Plot the fitted modal peak
            self.circle_plot_modal_peak.setData(self.modal_peaks[self.tableWidget.currentRow()]["data"].real[self.fit_lower:self.fit_upper],
                                                self.modal_peaks[self.tableWidget.currentRow()]["data"].imag[self.fit_lower:self.fit_upper],
                                                pen=pg.mkPen('r', width=1.5))

            self.modal_peaks[self.tableWidget.currentRow()]["plot1"].setData(self.w_fit,
                                                                             to_dB(np.abs(self.modal_peaks[self.tableWidget.currentRow()]["data"])),
                                                                             pen='r')
            self.modal_peaks[self.tableWidget.currentRow()]["plot2"].setData(self.w_fit,
                                                                             to_dB(np.abs(self.modal_peaks[self.tableWidget.currentRow()]["data"])),
                                                                             pen='r')

            # Update the constructed transfer function
            if self.show_transfer_fn_checkbox.isChecked():
                self.construct_transfer_fn()

    def update_from_plot(self):
        # Recalculate the geometric circle fit
        self.x0, self.y0, self.R0 = circle_fit(self.a_reg)

        # Recalculate the parameters
        wr, zr, cr, phi = self.sdof_get_parameters()

        if self.fit_controls_freq_combobox.currentText() == "Automatic":
            self.modal_peaks[self.tableWidget.currentRow()]["wr"] = wr
        if self.fit_controls_z_combobox.currentText() == "Automatic":
            self.modal_peaks[self.tableWidget.currentRow()]["zr"] = zr
        if self.fit_controls_amp_combobox.currentText() == "Automatic":
            self.modal_peaks[self.tableWidget.currentRow()]["cr"] = cr
        if self.fit_controls_phase_combobox.currentText() == "Automatic":
            self.modal_peaks[self.tableWidget.currentRow()]["phi"] = phi

        self.row_list[self.tableWidget.currentRow()]["freqbox"].setValue(self.modal_peaks[self.tableWidget.currentRow()]["wr"])
        self.row_list[self.tableWidget.currentRow()]["zbox"].setValue(self.modal_peaks[self.tableWidget.currentRow()]["zr"])
        self.row_list[self.tableWidget.currentRow()]["ampbox"].setValue(self.modal_peaks[self.tableWidget.currentRow()]["cr"])
        self.row_list[self.tableWidget.currentRow()]["phasebox"].setValue(self.modal_peaks[self.tableWidget.currentRow()]["phi"])



    def update_from_row(self, value):
        if self.sender() == self.row_list[self.tableWidget.currentRow()]["freqbox"]:
            self.modal_peaks[self.tableWidget.currentRow()]["wr"] = value
        if self.sender() == self.row_list[self.tableWidget.currentRow()]["zbox"]:
            self.modal_peaks[self.tableWidget.currentRow()]["zr"] = value
        if self.sender() == self.row_list[self.tableWidget.currentRow()]["ampbox"]:
            self.modal_peaks[self.tableWidget.currentRow()]["cr"] = value
        if self.sender() == self.row_list[self.tableWidget.currentRow()]["phasebox"]:
            self.modal_peaks[self.tableWidget.currentRow()]["phi"] = value


# Fitting functions -----------------------------------------------------------
    def single_pole(self, w, wr, zr, cr, phi):
        return (-cr*np.exp(1j*phi) / (2*wr)) / (w - wr*(1 + 1j*zr))

    def fitted_single_pole(self, w, wr, zr, cr, phi):
        return self.x0 + 1j*self.y0 - self.R0*np.exp(1j*(phi - np.pi/2))\
            + self.single_pole(w, wr, zr, cr, phi)

    def fitted_double_pole(self, w, wr, zr, cr, phi):
        return self.x0 + 1j*self.y0 - self.R0*np.exp(1j*(phi - np.pi/2))\
            + sdof_modal_peak(w, wr, zr, cr, phi)

    def optimise_single_pole_fit(self, w, wr, zr, cr, phi):
        if cr < 0:
            cr *= -1
            phi = (phi + np.pi/2) % np.pi

        f = self.fitted_single_pole(w, wr, zr, cr, phi)
        #return np.abs(f)
        return np.append(f.real, f.imag)

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
        #phi0 = np.angle(self.a_reg[i])
        phi0 = 0
        # First guess of damping factor of 1% (Q of 100)
        zr0 = 0.01

        # # Find the parameter values that give a minimum of
        # the optimisation function
        wr, zr, cr, phi = curve_fit(self.optimise_single_pole_fit,
                                    self.w_reg,
                                    #np.abs(self.a_reg),
                                    np.append(self.a_reg.real, self.a_reg.imag),
                                    [wr0, zr0, cr0, phi0],
                                    bounds=([self.w_reg.min(), 0, 0, -np.pi], [self.w_reg.max(), np.inf, np.inf, np.pi]))[0]

        return wr, zr, cr, phi


if __name__ == '__main__':
    app = 0

    app = QApplication(sys.argv)
    c = CircleFitWidget()
    c.showMaximized()
    """

    w = np.linspace(0, 25, 3e2)
    transfer_function = sdof_modal_peak(w, 5, 0.01, 100, 0.01)
    c.set_data(w, transfer_function)

    # Create a demo transfer function
    w = np.linspace(0, 25, 3e2)
    a = sdof_modal_peak(w, 5, 0.006, 8e12, np.pi/2) \
        + sdof_modal_peak(w, 10, 0.008, 8e12, 0) \
        + sdof_modal_peak(w, 12, 0.003, -8e12, 0) \
        + sdof_modal_peak(w, 20, 0.01, 22e12, 0) \
        # + 5e10*np.random.normal(size=w.size)
    c.set_data(w, a)
    """
    cs = ChannelSet()
    import_from_mat("//cued-fs/users/general/tab53/ts-home/Documents/owncloud/Documents/urop/labs/4c6/transfer_function_clean.mat", cs)
    a = cs.chans[0].data('f')
    c.set_data(np.linspace(0, cs.chans[0].sample_freq[0], a.size), a)
    #"""
    sys.exit(app.exec_())
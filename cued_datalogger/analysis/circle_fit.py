import sys, traceback
if __name__ == '__main__':
    sys.path.append('../../')

from cued_datalogger.api.channel import ChannelSet
from cued_datalogger.api.workspace import Workspace
from cued_datalogger.api.file_import import import_from_mat
from cued_datalogger.api.toolbox import Toolbox
from cued_datalogger.api.numpy_extensions import from_dB, to_dB, sdof_modal_peak
from cued_datalogger.api.pyqtgraph_extensions import InteractivePlotWidget

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QTableWidget,
                             QDoubleSpinBox, QCheckBox, QPushButton, QGroupBox,
                             QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QFileDialog, QTreeWidget, QTreeWidgetItem, QRadioButton)

import numpy as np
import scipy.optimize as so

from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
defaultpen='k'


def fit_circle_to_data(x, y):
    """
    Fit a geometric circle to the data given in x, y.

    Parameters
    ----------
    x : ndarray
    y : ndarray

    Returns
    -------
    x0 : float
        The x-coordinate of the centre of the circle.
    y0 : float
        The y-coordinate of the centre of the circle.
    R0 : float
        The radius of the circle.

    Notes
    -----
    This function solves a standard eigenvector formulation of the circle fit
    problem. See [1]_ for the derivation.

    References
    ----------
    .. [1]  Maia, N.M.M., Silva, J.M.M. et al, Theoretical and Experimental
       Modal Analysis, p221, Research Studies Press, 1997.
    """
    # Use the method from "Theoretical and Experimental Modal Analysis" p221
    # Set up the matrices
    xs = np.sum(x)
    ys = np.sum(y)
    xx = np.square(x).sum()
    yy = np.square(y).sum()
    xy = np.sum(x*y)
    L = x.size
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


class CircleFitWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()

        self.omega = np.zeros(1)
        self.transfer_function = np.zeros(1)
        self.channels = []
        self.current_peak = 0

        self.init_ui()

    def init_ui(self):
        # # Transfer function plot
        self.transfer_function_plotwidget = \
            InteractivePlotWidget(parent=self,
                                  title="Transfer Function",
                                  labels={'bottom': ("Frequency", "Hz"),
                                          'left': ("Transfer Function", "dB")})

        self.transfer_function_plot = \
            self.transfer_function_plotwidget.getPlotItem()

        self.transfer_function_plotwidget.sig_region_changed.connect(self.update_from_region)

        # # Nyquist plot
        self.nyquist_plotwidget = \
            InteractivePlotWidget(parent=self,
                                  show_region=False,
                                  show_crosshair=False,
                                  title="Circle fit",
                                  labels={'bottom': ("Re"),
                                          'left': ("Im")})

        self.nyquist_plot = self.nyquist_plotwidget.getPlotItem()
        self.nyquist_plot.setLimits(xMin=None, xMax=None,
                                    yMin=None, yMax=None,
                                    minXRange=None, maxXRange=None,
                                    minYRange=None, maxYRange=None)
        self.nyquist_plot.setAspectLocked(lock=True, ratio=1)
        self.nyquist_plot.showGrid(x=True, y=True)

        # # Create the items for the plots
        # The item for the raw transfer function
        self.transfer_function_list = []

        # The item for the reconstructed transfer function
        self.constructed_transfer_function = \
            pg.PlotDataItem(pen=pg.mkPen(width=3, style=Qt.DashLine))
        self.transfer_function_plot.addItem(self.constructed_transfer_function)

        # The item for the fitted peaks
        self.peaks = []

        # The item for the raw circle plot
        self.nyquist_plot_list = []

        # The item for the fitted circles
        self.nyquist_plot_peaks_list = []

        # # Table of results
        self.results = CircleFitResults(self)
        self.results.sig_selected_peak_changed.connect(self.set_current_peak)
        self.results.sig_recalculate_fit.connect(self.update_from_region)
        self.results.sig_add_new_peak.connect(self.add_new_peak)
        self.results.sig_manual_parameter_change.connect(self.update_from_table)

        # # Widget layout
        layout = QGridLayout()
        layout.addWidget(self.transfer_function_plotwidget, 0, 0, 1, 2)
        layout.addWidget(self.results, 1, 0)
        layout.addWidget(self.nyquist_plotwidget, 1, 1)
        self.setLayout(layout)

        self.setWindowTitle('Circle fit')
        self.show()

    def test_slot(*args, **kwargs):
        print("Test slot: {}, {}".format(args, kwargs))

    def show_transfer_fn(self, visible=True):
        print("Setting transfer function visible to " + str(visible))
        self.constructed_transfer_fn.setVisible(visible)

    def construct_transfer_fn(self):
        pass

    def add_new_peak(self):
        lower, upper = self.transfer_function_plotwidget.getRegionBounds()
        self.update_from_region(lower, upper)

    def update_from_region(self, region_lower_bound, region_upper_bound):
        for i, channel in enumerate(self.channels):
            self.freq = channel.data("frequency")
            self.omega = channel.data("omega")
            self.transfer_function = channel.data("transfer_function")
            self.transfer_function_type = channel.transfer_function_type

            f_in_region = (self.freq >= region_lower_bound) \
                              & (self.freq <= region_upper_bound)

            self.omega_reg = np.extract(f_in_region, self.omega)
            self.transfer_function_reg = np.extract(f_in_region, self.transfer_function)

            try:
                # Recalculate the geometric circle fit
                self.x0, self.y0, self.R0 = fit_circle_to_data(self.transfer_function_reg.real,
                                                               self.transfer_function_reg.imag)
            except:
                print("Error in fitting geometric circle.")
                traceback.print_exc()
            # Recalculate the parameters
            try:
                wr, zr, cr, phi = self.sdof_get_parameters()

                # Update the results table
                self.results.set_omega(self.current_peak, i, wr)
                self.results.set_damping(self.current_peak, i, zr)
                self.results.set_amplitude(self.current_peak, i, cr)
                self.results.set_phase_rad(self.current_peak, i, phi)

                print("Calculated: wr {}, zr {}, cr {}, phi {}".format(wr, zr, cr, phi))

            except:
                print("Error in calculating parameters.")
                traceback.print_exc()

            wr = self.results.get_omega(self.current_peak, i)
            zr = self.results.get_damping(self.current_peak, i)
            cr = self.results.get_amplitude(self.current_peak, i)
            phi = self.results.get_phase_rad(self.current_peak, i)

            print("Plotting: wr {}, zr {}, cr {}, phi {}".format(wr, zr, cr, phi))


            # Update the peak
            w_fit = np.linspace(self.omega.min(), self.omega.max(), self.omega.size*10)
            peak = sdof_modal_peak(w_fit, wr, zr, cr, phi)
            self.peaks[i].setData(w_fit / (2*np.pi), to_dB(np.abs(peak)))
            self.nyquist_plot_peaks_list[i].setData(peak.real, peak.imag)

            # Update what is displayed on the nyquist plot
            self.nyquist_plot_list[i].setData(self.transfer_function_reg.real, self.transfer_function_reg.imag)

            self.nyquist_plot.autoRange()

    def update_from_table(self):
        for i, channel in enumerate(self.channels):
            wr = self.results.get_omega(self.current_peak, i)
            zr = self.results.get_damping(self.current_peak, i)
            cr = self.results.get_amplitude(self.current_peak, i)
            phi = self.results.get_phase_rad(self.current_peak, i)

            # Update the peak
            peak = sdof_modal_peak(self.omega, wr, zr, cr, phi)
            self.peaks[i].setData(self.freq, to_dB(np.abs(peak)))
            self.nyquist_plot_peaks_list[i].setData(peak.real, peak.imag)

    def refresh_nyquist_plot(self):
        """Clear the nyquist plot and add the items back in."""
        self.nyquist_plotwidget.clear()

        for item in self.nyquist_plot_list:
            self.nyquist_plot.addItem(item)

        for item in self.nyquist_plot_peaks_list:
            self.nyquist_plot.addItem(item)

        self.nyquist_plot.autoRange()

    def refresh_transfer_function_plot(self):
        """Clear the transfer function plot and add the items back in."""
        self.transfer_function_plotwidget.clear()

        self.transfer_function_plot.addItem(self.constructed_transfer_function)

        for item in self.transfer_function_list:
            self.transfer_function_plot.addItem(item)

        for item in self.peaks:
            self.transfer_function_plot.addItem(item)

        self.transfer_function_plot.autoRange()

    def fitted_sdof_peak(self, w, wr, zr, cr, phi):
        """An SDOF modal peak fitted to the data using the geometric circle."""
        if self.transfer_function_type == 'displacement':
            return self.x0 + 1j*self.y0 - self.R0*np.exp(1j*(phi - np.pi/2))\
                + sdof_modal_peak(w, wr, zr, cr, phi)

        if self.transfer_function_type == 'velocity':
            return self.x0 + 1j*self.y0 - self.R0*np.exp(1j*phi)\
                + 1j*w*sdof_modal_peak(w, wr, zr, cr, phi)

        if self.transfer_function_type == 'acceleration':
            return self.x0 + 1j*self.y0 - self.R0*np.exp(1j*(phi + np.pi/2))\
                -w**2*sdof_modal_peak(w, wr, zr, cr, phi)

    def residuals(self, parameters):
        """The error function for least squares fitting."""
        wr = parameters[0]
        zr = np.abs(parameters[1])
        cr = parameters[2]
        phi = parameters[3]
        if cr < 0:
            cr *= -1
            phi = (phi + np.pi) % np.pi
        f = self.fitted_sdof_peak(self.omega_reg, wr, zr, cr, phi) - self.transfer_function_reg
        return np.sum(f*f.conj()).real


    def sdof_get_parameters(self):
        """Fit a SDOF peak to the data with a least squares fit, using values
        from the current peak as a first guess."""
        # # Find initial parameters for curve fitting
        # Find where the peak is - the maximum magnitude of the amplitude
        # within the region
        i = np.where(np.abs(self.transfer_function_reg) == np.abs(self.transfer_function_reg).max())[0][0]
        # Take the frequency at the max amplitude as a
        # first resonant frequency guess
        wr0 = self.omega_reg[i]
        # Take the max amplitude as a first guess for the modal constant
        cr0 = np.abs(from_dB(self.transfer_function_reg[i]))
        phi0 = np.angle(self.transfer_function_reg[i])
        # First guess of damping factor of 1% (Q of 100)
        zr0 = 0.01

        parameters0 = [wr0, zr0, cr0, phi0]

        # TODO: Fitting the curve is absolutely rubbish at the moment.
        #wr, zr, cr, phi = so.minimize(self.residuals, parameters0).x
        wr, zr, cr, phi = \
            so.minimize(self.residuals, parameters0, method='SLSQP',
                        bounds=[(self.omega_reg.min(), self.omega_reg.max()),
                                (None, None),
                                (None, None),
                                (None, None)]).x

        return wr, np.abs(zr), cr, phi

    def set_selected_channels(self, selected_channels):
        """Update which channels are plotted."""
        self.channels = []
        if selected_channels:
            for channel in selected_channels:
                if channel.is_dataset("transfer_function"):
                    self.channels.append(channel)

        self.results.channels = self.channels

        # # Populate the plot lists
        self.transfer_function_list = []
        self.nyquist_plot_list = []
        self.peaks = []
        self.nyquist_plot_peaks_list = []
        for channel in self.channels:
            transfer_function = pg.PlotDataItem(channel.data("frequency"),
                                                to_dB(np.abs(channel.data("transfer_function"))),
                                                pen=channel.colour)
            self.transfer_function_list.append(transfer_function)

            nyquist_plot = pg.PlotDataItem(channel.data("transfer_function").real,
                                           channel.data("transfer_function").imag,
                                           pen=None,
                                           symbol='o',
                                           symbolPen=None,
                                           symbolBrush=pg.mkBrush(channel.colour),
                                           symbolSize=7)
            self.nyquist_plot_list.append(nyquist_plot)

            self.peaks.append(pg.PlotDataItem(pen='k'))
            self.nyquist_plot_peaks_list.append(pg.PlotDataItem(pen='k'))

        self.refresh_transfer_function_plot()
        self.refresh_nyquist_plot()

    def set_current_peak(self, current_peak):
        self.current_peak = current_peak

class CircleFitResults(QGroupBox):
    """
    The tree displaying the Circle Fit results and the parameters used for
    automatically fitting the circle.

    Attributes
    ----------
    sig_selected_peak_changed : pyqtSignal(int)
        The signal emitted when the selected peak is changed.
    sig_recalculate_fit : pyqtSignal
        Signal emitted when the fit is forced to be recalculated.
    sig_add_new_peak : pyqtSignal
        Signal emitted when a new peak is added.
    sig_manual_parameter_change : pyqtSignal
        Signal emitted when a parameter is changed by hand.
    """

    sig_selected_peak_changed = pyqtSignal(int)
    sig_recalculate_fit = pyqtSignal()
    sig_add_new_peak = pyqtSignal()
    sig_manual_parameter_change = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Results", parent)

        self.channels = []
        self.num_peaks = 0

        self.init_ui()

    def init_ui(self):
        # # Tree for values
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name",
                                   "Frequency (Hz)",
                                   "Damping ratio",
                                   "Amplitude",
                                   "Phase (deg)",
                                   "Select"])

        self.tree.setStyleSheet("QTreeWidget::item:has-children "
                                "{ background-color : palette(mid);}")

        # # Tree for autofit parameters
        self.autofit_tree = QTreeWidget()
        self.autofit_tree.setHeaderLabels(["Name",
                                           "Frequency (Hz)",
                                           "Damping ratio",
                                           "Amplitude",
                                           "Phase (deg)",
                                           "Select"])

        self.autofit_tree.hide()
        self.autofit_tree.setStyleSheet("QTreeWidget::item:has-children "
                                        "{ background-color : palette(mid);}")

        # Connect the two trees together, so the views look identical
        self.autofit_tree.itemCollapsed.connect(self.on_item_collapsed)
        self.autofit_tree.itemExpanded.connect(self.on_item_expanded)
        self.tree.itemCollapsed.connect(self.on_item_collapsed)
        self.tree.itemExpanded.connect(self.on_item_expanded)

        # # Controls
        self.add_peak_btn = QPushButton("Add new peak", self)
        self.add_peak_btn.clicked.connect(self.add_peak)

        self.delete_selected_btn = QPushButton("Delete selected", self)
        self.delete_selected_btn.clicked.connect(self.delete_selected)

        self.view_autofit_btn = QPushButton("View autofit parameters", self)
        self.view_autofit_btn.clicked.connect(self.toggle_view)

        self.reset_to_autofit_btn = QPushButton("Reset all to auto", self)
        self.reset_to_autofit_btn.clicked.connect(self.reset_to_autofit)
        self.reset_to_autofit_btn.hide()

        controls1 = QGridLayout()
        controls1.addWidget(self.add_peak_btn, 0, 0)
        controls1.setColumnStretch(1, 1)
        controls1.addWidget(self.delete_selected_btn, 0, 2)

        controls2 = QGridLayout()
        controls2.setColumnStretch(0, 1)
        controls2.addWidget(self.reset_to_autofit_btn, 0, 1)
        controls2.addWidget(self.view_autofit_btn, 0, 2)

        # # Layout
        layout = QGridLayout()
        layout.addLayout(controls2, 0, 0)
        layout.addWidget(self.tree, 1, 0)
        layout.addWidget(self.autofit_tree, 1, 0)
        layout.addLayout(controls1, 2, 0)

        self.setLayout(layout)

    def add_peak(self):
        """Add a top-level item for a new peak to the tree, with children for
        each channel."""
        # Create the parent item for the peak
        peak_item = QTreeWidgetItem(self.tree,
                                    ["Peak {}".format(self.num_peaks),
                                     "", "", "", "", ""])
        autofit_peak_item = QTreeWidgetItem(self.autofit_tree,
                                            ["Peak {}".format(self.num_peaks),
                                             "", "", "", "", ""])

        # Put a radio button in column 5 in the tree
        radio_btn = QRadioButton()
        radio_btn.toggled.connect(self.on_selected_peak_changed)
        self.tree.setItemWidget(peak_item, 5, radio_btn)
        radio_btn.setChecked(True)

        for col in [1, 2, 3, 4]:
            # Put comboboxes in the autofit tree
            combobox = QComboBox()
            combobox.addItems(["Auto", "Manual"])
            combobox.currentIndexChanged.connect(self.update_peak_average)
            self.autofit_tree.setItemWidget(autofit_peak_item, col, combobox)

        # Put spinboxes in the tree
        freq_spinbox = QDoubleSpinBox()
        freq_spinbox.setRange(0, 9e99)
        freq_spinbox.valueChanged.connect(self.sig_manual_parameter_change.emit)
        self.tree.setItemWidget(peak_item, 1, freq_spinbox)
        damping_spinbox = QDoubleSpinBox()
        damping_spinbox.setRange(0, 9e99)
        damping_spinbox.setDecimals(5)
        damping_spinbox.setSingleStep(0.00001)
        damping_spinbox.valueChanged.connect(self.sig_manual_parameter_change.emit)
        self.tree.setItemWidget(peak_item, 2, damping_spinbox)
        amp_spinbox = QDoubleSpinBox()
        amp_spinbox.setRange(0, 9e99)
        amp_spinbox.valueChanged.connect(self.sig_manual_parameter_change.emit)
        self.tree.setItemWidget(peak_item, 3, amp_spinbox)
        phase_spinbox = QDoubleSpinBox()
        phase_spinbox.setRange(-180, 180)
        phase_spinbox.valueChanged.connect(self.sig_manual_parameter_change.emit)
        phase_spinbox.setWrapping(True)
        self.tree.setItemWidget(peak_item, 4, phase_spinbox)

        # Create the child items for each channel for this peak if there's
        # more than one channel
        if len(self.channels) > 1:
            for channel in self.channels:
                channel_item = QTreeWidgetItem(peak_item,
                                               [channel.name,
                                                "", "", "", "", ""])
                autofit_channel_item = QTreeWidgetItem(autofit_peak_item,
                                                       [channel.name,
                                                        "", "", "", "", ""])
                for col in [1, 2, 3, 4]:
                    # Put comboboxes in the autofit tree
                    combobox = QComboBox()
                    combobox.addItems(["Auto", "Manual"])
                    combobox.currentIndexChanged.connect(self.update_peak_average)
                    self.autofit_tree.setItemWidget(autofit_channel_item,
                                                    col, combobox)

                freq_spinbox = QDoubleSpinBox()
                freq_spinbox.setRange(0, 9e99)
                freq_spinbox.valueChanged.connect(self.sig_manual_parameter_change.emit)
                freq_spinbox.valueChanged.connect(self.update_peak_average)
                self.tree.setItemWidget(channel_item, 1, freq_spinbox)
                damping_spinbox = QDoubleSpinBox()
                damping_spinbox.setRange(0, 9e99)
                damping_spinbox.setDecimals(5)
                damping_spinbox.setSingleStep(0.00001)
                damping_spinbox.valueChanged.connect(self.sig_manual_parameter_change.emit)
                damping_spinbox.valueChanged.connect(self.update_peak_average)
                self.tree.setItemWidget(channel_item, 2, damping_spinbox)
                amp_spinbox = QDoubleSpinBox()
                amp_spinbox.setRange(0, 9e99)
                amp_spinbox.valueChanged.connect(self.sig_manual_parameter_change.emit)
                amp_spinbox.valueChanged.connect(self.update_peak_average)
                self.tree.setItemWidget(channel_item, 3, amp_spinbox)
                phase_spinbox = QDoubleSpinBox()
                phase_spinbox.setRange(-180, 180)
                phase_spinbox.setWrapping(True)
                phase_spinbox.valueChanged.connect(self.sig_manual_parameter_change.emit)
                phase_spinbox.valueChanged.connect(self.update_peak_average)
                self.tree.setItemWidget(channel_item, 4, phase_spinbox)

        # Register that we've added another peak
        self.num_peaks += 1
        self.sig_add_new_peak.emit()

    def delete_selected(self):
        """Delete the item that is currently selected."""
        for i in range(self.tree.topLevelItemCount()):
            # If the radio button is checked
            peak_item = self.tree.topLevelItem(i)
            if peak_item is not None:
                if self.tree.itemWidget(peak_item, 5).isChecked():
                    # Delete this item
                    self.tree.takeTopLevelItem(i)
                    self.autofit_tree.takeTopLevelItem(i)
                    # self.num_peaks -= 1

    def toggle_view(self):
        if self.tree.isVisible():
            self.tree.hide()
            self.autofit_tree.show()
            self.reset_to_autofit_btn.show()
            self.view_autofit_btn.setText("View parameter values")
        else:
            self.tree.show()
            self.autofit_tree.hide()
            self.reset_to_autofit_btn.hide()
            self.view_autofit_btn.setText("View autofit parameters")

    def on_item_collapsed(self, item):
        index = self.sender().indexOfTopLevelItem(item)
        self.tree.collapseItem(self.tree.topLevelItem(index))
        self.autofit_tree.collapseItem(self.autofit_tree.topLevelItem(index))

    def on_item_expanded(self, item):
        index = self.sender().indexOfTopLevelItem(item)
        self.tree.expandItem(self.tree.topLevelItem(index))
        self.autofit_tree.expandItem(self.autofit_tree.topLevelItem(index))

    def on_selected_peak_changed(self, checked):
        for i in range(self.tree.topLevelItemCount()):
            # If the radio button in this row is the sender
            peak_item = self.tree.topLevelItem(i)
            if peak_item is not None:
                if self.tree.itemWidget(peak_item, 5) == self.sender():
                    if checked:
                        print("Selected peak: " + str(i))
                        self.sig_selected_peak_changed.emit(i)

    def reset_to_autofit(self):
        """Reset all parameters to be automatically adjusted."""
        for peak_number in range(self.num_peaks):
            peak_item = self.autofit_tree.topLevelItem(peak_number)

            for col in [1, 2, 3, 4]:
                self.autofit_tree.itemWidget(peak_item, col).setCurrentIndex(0)

            if len(self.channels) > 1:
                for channel_number in range(len(self.channels)):
                    channel_item = peak_item.child(channel_number)
                    for col in [1, 2, 3, 4]:
                        self.autofit_tree.itemWidget(channel_item, col).setCurrentIndex(0)

        self.sig_recalculate_fit.emit()

    def update_peak_average(self):
        """Set the parameter values displayed for the peak to the average of
        all the channel values for each parameter."""
        for peak_number in range(self.num_peaks):
            # Get the peak item
            peak_item = self.tree.topLevelItem(peak_number)
            autofit_item = self.autofit_tree.topLevelItem(peak_number)

            if peak_item is not None:
                # Find the average values of all the channels
                avg_freq = 0
                avg_damping = 0
                avg_amplitude = 0
                avg_phase_deg = 0

                for channel_number in range(len(self.channels)):
                    avg_freq += self.get_frequency(peak_number, channel_number)
                    avg_damping += self.get_damping(peak_number, channel_number)
                    avg_amplitude += self.get_amplitude(peak_number, channel_number)
                    avg_phase_deg += self.get_phase_deg(peak_number, channel_number)

                avg_freq /= len(self.channels)
                avg_damping /= len(self.channels)
                avg_amplitude /= len(self.channels)
                avg_phase_deg /= len(self.channels)

                # Set the peak item to display the averages
                if self.autofit_tree.itemWidget(autofit_item, 1).currentText() == "Auto":
                    self.tree.itemWidget(peak_item, 1).setValue(avg_freq)
                if self.autofit_tree.itemWidget(autofit_item, 2).currentText() == "Auto":
                    self.tree.itemWidget(peak_item, 2).setValue(avg_damping)
                if self.autofit_tree.itemWidget(autofit_item, 3).currentText() == "Auto":
                    self.tree.itemWidget(peak_item, 3).setValue(avg_amplitude)
                if self.autofit_tree.itemWidget(autofit_item, 4).currentText() == "Auto":
                    self.tree.itemWidget(peak_item, 4).setValue(avg_phase_deg)

    def get_frequency(self, peak_number, channel_number=None):
        """Return the resonant frequency (Hz) of the peak given by
        *peak_number*. If *channel_number* is given, return the resonant
        frequency of the given peak in the given channel."""
        peak_item = self.tree.topLevelItem(peak_number)
        if peak_item is not None:
            if peak_item.childCount():
                channel_item = peak_item.child(channel_number)
            else:
                channel_item = peak_item
            spinbox = self.tree.itemWidget(channel_item, 1)
            return spinbox.value()
        else:
            return 0

    def get_omega(self, peak_number, channel_number=None):
        """Return the resonant frequency (rads) of the peak given by
        *peak_number*. If *channel_number* is given, return the resonant
        frequency of the given peak in the given channel."""
        peak_item = self.tree.topLevelItem(peak_number)
        if peak_item is not None:
            if peak_item.childCount():
                channel_item = peak_item.child(channel_number)
            else:
                channel_item = peak_item
            spinbox = self.tree.itemWidget(channel_item, 1)
            return spinbox.value() * 2*np.pi
        else:
            return 0

    def get_damping(self, peak_number, channel_number=None):
        """Return the damping ratio of the peak given by *peak_number*. If
        *channel_number* is given, return the damping ratio of the given peak
        in the given channel."""
        peak_item = self.tree.topLevelItem(peak_number)
        if peak_item is not None:
            if peak_item.childCount():
                channel_item = peak_item.child(channel_number)
            else:
                channel_item = peak_item
            spinbox = self.tree.itemWidget(channel_item, 2)
            return spinbox.value()
        else:
            return 0


    def get_amplitude(self, peak_number, channel_number=None):
        """Return the amplitude of the peak given by *peak_number*. If
        *channel_number* is given, return the amplitude of the given peak in
        the given channel."""
        peak_item = self.tree.topLevelItem(peak_number)
        if peak_item is not None:
            if peak_item.childCount():
                channel_item = peak_item.child(channel_number)
            else:
                channel_item = peak_item
            spinbox = self.tree.itemWidget(channel_item, 3)
            return spinbox.value()
        else:
            return 0

    def get_phase_deg(self, peak_number, channel_number=None):
        """Return the phase (deg) of the peak given by *peak_number*. If
        *channel_number* is given, return the phase of the given peak in the
        given channel."""
        peak_item = self.tree.topLevelItem(peak_number)
        if peak_item is not None:
            if peak_item.childCount():
                channel_item = peak_item.child(channel_number)
            else:
                channel_item = peak_item
            spinbox = self.tree.itemWidget(channel_item, 4)
            return spinbox.value()
        else:
            return 0

    def get_phase_rad(self, peak_number, channel_number=None):
        """Return the phase (rad) of the peak given by *peak_number*. If
        *channel_number* is given, return the phase of the given peak in the
        given channel."""
        peak_item = self.tree.topLevelItem(peak_number)
        if peak_item is not None:
            if peak_item.childCount():
                channel_item = peak_item.child(channel_number)
            else:
                channel_item = peak_item
            spinbox = self.tree.itemWidget(channel_item, 4)
            return np.deg2rad(spinbox.value())
        else:
            return 0

    def set_frequency(self, peak_number, channel_number=None, value=0):
        """Set the frequency (Hz) of a given peak to *value*. If *channel_number* is
        given, set the frequency of the given peak in the given channel."""
        # Get the top level items
        peak_item = self.tree.topLevelItem(peak_number)
        autofit_peak_item = self.autofit_tree.topLevelItem(peak_number)
        # Check they exist
        if peak_item is not None:
            if peak_item.childCount():
                channel_item = peak_item.child(channel_number)
            else:
                channel_item = peak_item
            if autofit_peak_item.childCount():
                autofit_channel_item = autofit_peak_item.child(channel_number)
            else:
                autofit_channel_item = autofit_peak_item
            # Set the value only if the combobox is set to autofit
            combobox = \
                self.autofit_tree.itemWidget(autofit_channel_item, 1)
            if combobox.currentText() == "Auto":
                spinbox = self.tree.itemWidget(channel_item, 1)
                spinbox.setValue(value)

    def set_omega(self, peak_number, channel_number=None, value=0):
        """Set the frequency (rad) of a given peak to *value*. If *channel_number* is
        given, set the frequency of the given peak in the given channel."""
        # Get the top level items
        peak_item = self.tree.topLevelItem(peak_number)
        autofit_peak_item = self.autofit_tree.topLevelItem(peak_number)
        # Check they exist
        if peak_item is not None:
            if peak_item.childCount():
                channel_item = peak_item.child(channel_number)
            else:
                channel_item = peak_item
            if autofit_peak_item.childCount():
                autofit_channel_item = autofit_peak_item.child(channel_number)
            else:
                autofit_channel_item = autofit_peak_item
            # Set the value only if the combobox is set to autofit
            combobox = \
                self.autofit_tree.itemWidget(autofit_channel_item, 1)
            if combobox.currentText() == "Auto":
                spinbox = self.tree.itemWidget(channel_item, 1)
                spinbox.setValue(value / (2*np.pi))

    def set_damping(self, peak_number, channel_number=None, value=0):
        """Set the damping ratio of a given peak to *value*. If *channel_number* is
        given, set the damping ratio of the given peak in the given channel."""
        # Get the top level items
        peak_item = self.tree.topLevelItem(peak_number)
        autofit_peak_item = self.autofit_tree.topLevelItem(peak_number)
        # Check they exist
        if peak_item is not None:
            if peak_item.childCount():
                channel_item = peak_item.child(channel_number)
            else:
                channel_item = peak_item
            if autofit_peak_item.childCount():
                autofit_channel_item = autofit_peak_item.child(channel_number)
            else:
                autofit_channel_item = autofit_peak_item
            # Set the value only if the combobox is set to autofit
            combobox = \
                self.autofit_tree.itemWidget(autofit_channel_item, 2)
            if combobox.currentText() == "Auto":
                spinbox = self.tree.itemWidget(channel_item, 2)
                spinbox.setValue(value)


    def set_amplitude(self, peak_number, channel_number=None, value=0):
        """Set the amplitude of a given peak to *value*. If *channel_number* is
        given, set the amplitude of the given peak in the given channel."""
        # Get the top level items
        peak_item = self.tree.topLevelItem(peak_number)
        autofit_peak_item = self.autofit_tree.topLevelItem(peak_number)
        # Check they exist
        if peak_item is not None:
            if peak_item.childCount():
                channel_item = peak_item.child(channel_number)
            else:
                channel_item = peak_item
            if autofit_peak_item.childCount():
                autofit_channel_item = autofit_peak_item.child(channel_number)
            else:
                autofit_channel_item = autofit_peak_item
            # Set the value only if the combobox is set to autofit
            combobox = \
                self.autofit_tree.itemWidget(autofit_channel_item, 3)
            if combobox.currentText() == "Auto":
                spinbox = self.tree.itemWidget(channel_item, 3)
                spinbox.setValue(value)

    def set_phase_deg(self, peak_number, channel_number=None, value=0):
        """Set the phase of a given peak to *value*. If *channel_number* is
        given, set the phase of the given peak in the given channel."""
        # Get the top level items
        peak_item = self.tree.topLevelItem(peak_number)
        autofit_peak_item = self.autofit_tree.topLevelItem(peak_number)
        # Check they exist
        if peak_item is not None:
            if peak_item.childCount():
                channel_item = peak_item.child(channel_number)
            else:
                channel_item = peak_item
            if autofit_peak_item.childCount():
                autofit_channel_item = autofit_peak_item.child(channel_number)
            else:
                autofit_channel_item = autofit_peak_item
            # Set the value only if the combobox is set to autofit
            combobox = \
                self.autofit_tree.itemWidget(autofit_channel_item, 4)
            if combobox.currentText() == "Auto":
                spinbox = self.tree.itemWidget(channel_item, 4)
                spinbox.setValue(value)


    def set_phase_rad(self, peak_number, channel_number=None, value=0):
        """Set the phase of a given peak to *value*. If *channel_number* is
        given, set the phase of the given peak in the given channel."""
        # Get the top level items
        peak_item = self.tree.topLevelItem(peak_number)
        autofit_peak_item = self.autofit_tree.topLevelItem(peak_number)
        # Check they exist
        if peak_item is not None:
            if peak_item.childCount():
                channel_item = peak_item.child(channel_number)
            else:
                channel_item = peak_item
            if autofit_peak_item.childCount():
                autofit_channel_item = autofit_peak_item.child(channel_number)
            else:
                autofit_channel_item = autofit_peak_item
            # Set the value only if the combobox is set to autofit
            combobox = \
                self.autofit_tree.itemWidget(autofit_channel_item, 4)
            if combobox.currentText() == "Auto":
                spinbox = self.tree.itemWidget(channel_item, 4)
                spinbox.setValue(np.rad2deg(value))


class CircleFitToolbox(Toolbox):
    """
    The Toolbox for the CircleFitWidget.

    This Toolbox contains the tools for controlling the circle fit. It has
    two tabs: 'Transfer Function', for tools relating to the construction
    of a transfer function, and 'Autofit Controls', which contains tools
    for controlling how the circle is fit to the data.

    Attributes
    ----------
    sig_construct_transfer_fn : pyqtSignal
      The signal emitted when a new transfer function is to be constructed.
    sig_show_transfer_fn : pyqtSignal(bool)
      The signal emitted when the visibility of the transfer function is
      changed. Format (visible).
    """

    sig_construct_transfer_fn = pyqtSignal()
    sig_show_transfer_fn = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.init_ui()

    def init_ui(self):
        self.init_transfer_function_tab()

    def init_transfer_function_tab(self):
        self.transfer_function_tab = QWidget()
        transfer_function_tab_layout = QGridLayout()

        self.construct_transfer_fn_btn = QPushButton()
        self.construct_transfer_fn_btn.setText("Construct transfer function")
        self.construct_transfer_fn_btn.clicked.connect(self.sig_construct_transfer_fn.emit)
        transfer_function_tab_layout.addWidget(self.construct_transfer_fn_btn, 0, 0)

        self.show_transfer_fn_checkbox = QCheckBox()
        self.show_transfer_fn_checkbox.setText("Show transfer function")
        self.show_transfer_fn_checkbox.stateChanged.connect(self.sig_show_transfer_fn.emit)
        transfer_function_tab_layout.addWidget(self.show_transfer_fn_checkbox, 1, 0)

        self.transfer_function_tab.setLayout(transfer_function_tab_layout)
        transfer_function_tab_layout.setColumnStretch(1, 1)
        transfer_function_tab_layout.setRowStretch(2, 1)

        self.addTab(self.transfer_function_tab, "Transfer function")


if __name__ == '__main__':
    CurrentWorkspace = Workspace()
    app = 0

    app = QApplication(sys.argv)
    c = CircleFitWidget()
    c.CurrentWorkspace = CurrentWorkspace
    c.showMaximized()

    cs = ChannelSet()

    #c.load_transfer_function(cs)
    import_from_mat("../../tests/transfer_function_grid.mat", cs)
    c.transfer_function_type = 'acceleration'
    c.set_selected_channels(cs.channels)
    #c.set_data(np.linspace(0, cs.channel_metadata(0, "sample_rate"), a.size), a)
    #"""
    sys.exit(app.exec_())

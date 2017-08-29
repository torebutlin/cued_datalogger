import sys
if __name__ == '__main__':
    sys.path.append('..')

from datalogger.api.channel import ChannelSet
from datalogger.api.workspace import Workspace
from datalogger.api.file_import import import_from_mat
from datalogger.api.toolbox import Toolbox
from datalogger.api.numpy_extensions import to_dB, sdof_modal_peak
from datalogger.api.pyqtgraph_extensions import InteractivePlotWidget

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QTableWidget,
                             QDoubleSpinBox, QCheckBox, QPushButton, QGroupBox,
                             QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QFileDialog, QTreeWidget, QTreeWidgetItem)

import numpy as np
from scipy.optimize import curve_fit

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

        self.w = np.zeros(1)
        self.autofit_parameters = set(["frequency", "z", "amplitude", "phase"])

        self.init_ui()

    def init_ui(self):
        # # Transfer function plot
        self.transfer_function_plotwidget = \
            InteractivePlotWidget(parent=self,
                                  title="Transfer Function",
                                  labels={'bottom': ("Frequency", "rad"),
                                          'left': ("Transfer Function", "dB")})
    
        self.transfer_function_plot = \
            self.transfer_function_plotwidget.getPlotItem()

        # # Nyquist plot
        self.nyquist_plotwidget = \
            InteractivePlotWidget(parent=self,
                                  show_region=False,
                                  show_crosshair=False,
                                  title="Circle fit",
                                  labels={'bottom': ("Re"),
                                          'left': ("Im")})
    
        self.nyquist_plot = self.nyquist_plotwidget.getPlotItem()
        self.nyquist_plot.setAspectLocked(lock=True, ratio=1)
        self.nyquist_plot.showGrid(x=True, y=True)

        # # Create the items for the plots
        # The item for the raw transfer function
        self.transfer_function = pg.PlotDataItem(pen=defaultpen)
        self.transfer_function_plot.addItem(self.transfer_function)

        # The item for the reconstructed transfer function
        self.constructed_transfer_function = pg.PlotDataItem(pen='b')
        self.transfer_function_plot.addItem(self.constructed_transfer_function)

        # The item for the raw circle plot
        self.nyquist_plot_points = pg.PlotDataItem()
        self.nyquist_plot.addItem(self.nyquist_plot_points)

        # The item for the current fit
        self.nyquist_plot_current_peak = pg.PlotDataItem()
        self.nyquist_plot.addItem(self.nyquist_plot_current_peak)

        # # Table of results
        self.results = CircleFitResults(self)

        # # Widget layout
        layout = QGridLayout()
        layout.addWidget(self.transfer_function_plotwidget, 0, 0, 2, 1)
        layout.addWidget(self.results, 2, 0)
        layout.addWidget(self.nyquist_plotwidget, 2, 1)
        self.setLayout(layout)

        self.setWindowTitle('Circle fit')
        self.show()

    # Interaction functions ---------------------------------------------------
    def add_peak(self):
        pass

    def show_transfer_fn(self, visible=True):
        print("Setting transfer function visible to " + str(visible))
        self.constructed_transfer_fn.setVisible(visible)

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
            """
            for item in self.region_select_plot.items:
                if item == self.modal_peaks[i]["plot2"]:
                    item.setVisible(checked)
            """

    def delete_selected(self):
        for i, row in enumerate(self.row_list):
            if row["selectbox"].isChecked():
                # Delete from table
                del self.row_list[i]
                self.tableWidget.removeRow(i)
                # Delete from graphs
                self.transfer_func_plot.removeItem(self.modal_peaks[i]["plot1"])
                #self.region_select_plot.removeItem(self.modal_peaks[i]["plot2"])
                del self.modal_peaks[i]
        # With pyqtgraph's removeItem, all the other items are set back to being visible
        # so need to undo this for those that are unchecked
        self.update_peak_selection()
        self.show_transfer_fn(True)

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
        self.transfer_function.setData(x=self.w,
                                        y=to_dB(np.abs(self.a)))

        #self.transfer_function2.setData(x=self.w,
        #                                y=to_dB(np.abs(self.a)))

        self.transfer_func_plot.autoRange()
        self.transfer_func_plot.setXRange(self.w.min(), self.w.max())
        self.transfer_func_plot.setLimits(xMin=self.w.min(), xMax=self.w.max())
        self.transfer_func_plot.disableAutoRange()

        #self.region_select_plot.autoRange()
        #self.region_select_plot.setXRange(self.w.min(), self.w.max())
        #self.region_select_plot.setLimits(xMin=self.w.min(), xMax=self.w.max())
        #self.region_select_plot.disableAutoRange()

        #self.region_select.setBounds((self.w.min(), self.w.max()))
        self.add_peak()

    def construct_transfer_fn(self):
        self.constructed_transfer_fn = np.zeros_like(self.modal_peaks[-1]["data"])
        for i, peak in enumerate(self.modal_peaks):
            if self.row_list[i]["selectbox"].isChecked():
                self.constructed_transfer_fn += peak["data"]

        self.constructed_transfer_fn.setData(x=self.w_fit,
                                              y=to_dB(np.abs(self.constructed_transfer_fn)))

    # Update functions --------------------------------------------------------
    def update_zoom(self):
        pass

    def autorange_to_region(self, checked):
        pass
        
    def update_region(self):
        pass

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
        try:
            lck_btn = self.row_list[self.tableWidget.currentRow()]["lockbtn"]
        except:
            lck_btn = None    
        # If the current peak is not locked
        if lck_btn and not lck_btn.isChecked():
            # Get zoomed in region
            self.get_viewed_region()

            # Update the values
            if self.sender() in self.row_list[self.tableWidget.currentRow()].values():
                self.update_from_row(value)
            else:
                self.update_from_plot()

            # Recalculate the fitted modal peak
            #self.modal_peaks[self.tableWidget.currentRow()]["data"] = self.fitted_sdof_peak(self.w_fit,
            self.modal_peaks[self.tableWidget.currentRow()]["data"] = -self.w_fit**2 * sdof_modal_peak(self.w_fit,
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
            if self.constructed_transfer_fn.isVisible():
                self.construct_transfer_fn()

    def update_from_plot(self):
        # Recalculate the geometric circle fit
        self.x0, self.y0, self.R0 = fit_circle_to_data(self.a_reg.real, self.a_reg.imag)

        # Recalculate the parameters
        wr, zr, cr, phi = self.sdof_get_parameters()

        if "frequency" in self.autofit_parameters:
            self.modal_peaks[self.tableWidget.currentRow()]["wr"] = wr
        if "z" in self.autofit_parameters:
            self.modal_peaks[self.tableWidget.currentRow()]["zr"] = zr
        if "amplitude" in self.autofit_parameters:
            self.modal_peaks[self.tableWidget.currentRow()]["cr"] = cr
        if "phase" in self.autofit_parameters:
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

    def update_autofit_parameters(self, autofit, parameter):
        if autofit:
            self.autofit_parameters.add(parameter)
        else:
            self.autofit_parameters.remove(parameter)            

# Fitting functions -----------------------------------------------------------
    def fitted_sdof_peak(self, w, wr, zr, cr, phi):
        if self.transfer_function_type == 'displacement':
            return self.x0 + 1j*self.y0 - self.R0*np.exp(1j*(phi - np.pi/2))\
                + sdof_modal_peak(w, wr, zr, cr, phi)

        if self.transfer_function_type == 'velocity':
            return self.x0 + 1j*self.y0 - self.R0*np.exp(1j*phi)\
                + 1j*w*sdof_modal_peak(w, wr, zr, cr, phi)

        if self.transfer_function_type == 'acceleration':
            return self.x0 + 1j*self.y0 - self.R0*np.exp(1j*(phi + np.pi/2))\
                -w**2*sdof_modal_peak(w, wr, zr, cr, phi)

    def optimise_sdof_peak_fit(self, w, wr, zr, cr, phi):
        if cr < 0:
            cr *= -1
            phi = (phi + np.pi) % np.pi
        f = self.fitted_sdof_peak(w, wr, zr, cr, phi)
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
        phi0 = np.angle(self.a_reg[i])
        #phi0 = 0
        # First guess of damping factor of 1% (Q of 100)
        zr0 = 0.01

        # # Find the parameter values that give a minimum of
        # the optimisation function
        wr, zr, cr, phi = curve_fit(self.optimise_sdof_peak_fit,
                                    self.w_reg,
                                    np.append(self.a_reg.real, self.a_reg.imag),
                                    [wr0, zr0, cr0, phi0],
                                    bounds=([self.w_reg.min(), 0, 0, -np.pi], [self.w_reg.max(), np.inf, np.inf, np.pi]))[0]

        return wr, zr, cr, phi


    def load_tf(self,cs):
        # Get a list of URLs from a QFileDialog
        url = QFileDialog.getOpenFileNames(self, "Load transfer function", "addons",
                                               "MAT Files (*.mat)")[0]
        print(url)
        
        try:
            import_from_mat(url, cs)
        except:
            print('Load failed. Revert to default!')
            import_from_mat("//cued-fs/users/general/tab53/ts-home/Documents/owncloud/Documents/urop/labs/4c6/transfer_function_clean.mat", cs)


class CircleFitResults(QGroupBox):
    """
    The tree of results for the Circle Fit.
    
    Attributes
    ----------
    sig_selected_peak_changed : pyqtSignal(int)
        The signal emitted when the selected peak is changed.
    """
    
    sig_selected_peak_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__("Results", parent)
        
        # TODO
        self.num_channels = 4
        self.num_peaks = 0
                
        self.init_ui()
    
    def init_ui(self):       
        # # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Frequency", "Damping ratio",
                                   "Amplitude", "Phase", "Select"])
        
        # # Controls
        self.add_peak_btn = QPushButton("Add new peak", self)
        self.add_peak_btn.clicked.connect(self.add_peak)

        self.delete_selected_btn = QPushButton("Delete selected", self)
        self.delete_selected_btn.clicked.connect(self.delete_selected)
        
        controls = QGridLayout()
        controls.addWidget(self.add_peak_btn, 0, 0)
        controls.setColumnStretch(1, 1)
        controls.addWidget(self.delete_selected_btn, 0, 2)
        
        # # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        layout.addLayout(controls)
        
        self.setLayout(layout)
    
    def add_peak(self):
        """Add a top-level item for a new peak to the tree, with children for
        each channel."""
        # Create the parent item for the peak
        peak_item = QTreeWidgetItem(self.tree, 
                                    ["Peak {}".format(self.num_peaks), 
                                     "", "", "", "", ""])
        # Put a radio button in column 5
        radio_btn = QRadioButton()
        radio_btn.toggled.connect(self.on_selected_peak_changed)
        self.tree.setItemWidget(peak_item, 5, radio_btn)
        
        # Put spinboxes in columns 1-4
        for col in [1,2,3,4]:
            spinbox = QDoubleSpinBox()
            self.tree.setItemWidget(peak_item, col, spinbox)
        
        # Create the child items for each channel for this peak if there's
        # more than one channel
        if self.num_channels > 1:
            for i in range(self.num_channels):
                channel_item = QTreeWidgetItem(peak_item,
                                               ["Channel {}".format(i),
                                                "", "", "", "", ""])
                # Put spinboxes in cols 1-4
                for col in [1,2,3,4]:
                    spinbox = QDoubleSpinBox()
                    spinbox.valueChanged.connect(self.update_peak_average)
                    self.tree.setItemWidget(channel_item, col, spinbox)
        
        # Register that we've added another peak
        self.num_peaks += 1
    
    def delete_selected(self):
        """Delete the item that is currently selected."""
        for i in range(self.tree.topLevelItemCount()):
            # If the radio button is checked
            peak_item = self.tree.topLevelItem(i)
            if peak_item is not None:
                if self.tree.itemWidget(peak_item, 5).isChecked():
                    # Delete this item
                    self.tree.takeTopLevelItem(i)
                    #self.num_peaks -= 1
    
    def on_selected_peak_changed(self, checked):
        for i in range(self.tree.topLevelItemCount()):
            # If the radio button in this row is the sender
            peak_item = self.tree.topLevelItem(i)
            if peak_item is not None:
                if self.tree.itemWidget(peak_item, 5) == self.sender():
                    if checked:
                        print("Selected: " + str(i))
                        self.sig_selected_peak_changed.emit(i)
                    else:
                        pass

    def update_parameter_values(self):
        pass
    
    def update_peak_average(self):
        """Set the parameter values displayed for the peak to the average of 
        all the channel values for each parameter."""
        for peak_number in range(self.num_peaks):
            # Get the peak item
            peak_item = self.tree.topLevelItem(peak_number)
            
            if peak_item is not None:
                # Find the average values of all the channels
                avg_frequency = 0
                avg_damping = 0
                avg_amplitude = 0
                avg_phase = 0
                
                for channel_number in range(self.num_channels):
                    avg_frequency += self.get_frequency(peak_number, channel_number)
                    avg_damping += self.get_damping(peak_number, channel_number)
                    avg_amplitude += self.get_amplitude(peak_number, channel_number)
                    avg_phase += self.get_phase(peak_number, channel_number)
                
                avg_frequency /= self.num_channels
                avg_damping /= self.num_channels
                avg_amplitude /= self.num_channels
                avg_phase /= self.num_channels
                
                # Set the peak item to display the averages
                self.tree.itemWidget(peak_item, 1).setValue(avg_frequency)
                self.tree.itemWidget(peak_item, 2).setValue(avg_damping)
                self.tree.itemWidget(peak_item, 3).setValue(avg_amplitude)
                self.tree.itemWidget(peak_item, 4).setValue(avg_phase)
    
    def get_frequency(self, peak_number, channel_number=None):
        """Return the resonant frequency of the peak given by 
        *peak_number*. If *channel_number* is given, return the resonant  
        frequency of the given peak in the given channel."""
        peak_item = self.tree.topLevelItem(peak_number)
        if peak_item is not None:
            if channel_number is None:
                spinbox = self.tree.itemWidget(peak_item, 1)
                return spinbox.value()
            else:
                channel_item = peak_item.child(channel_number)
                spinbox = self.tree.itemWidget(channel_item, 1)
                return spinbox.value()
        else:
            return 0
       
    def get_damping(self, peak_number, channel_number=None):
        """Return the damping ratio of the peak given by *peak_number*. If 
        *channel_number* is given, return the damping ratio of the given peak
        in the given channel."""
        peak_item = self.tree.topLevelItem(peak_number)
        if peak_item is not None:
            if channel_number is None:
                spinbox = self.tree.itemWidget(peak_item, 2)
                return spinbox.value()
            else:
                channel_item = peak_item.child(channel_number)
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
            if channel_number is None:
                spinbox = self.tree.itemWidget(peak_item, 3)
                return spinbox.value()
            else:
                channel_item = peak_item.child(channel_number)
                spinbox = self.tree.itemWidget(channel_item, 3)
                return spinbox.value()
        else:
            return 0
       
    def get_phase(self, peak_number, channel_number=None):
        """Return the phase of the peak given by *peak_number*. If 
        *channel_number* is given, return the phase of the given peak in the
        given channel."""
        peak_item = self.tree.topLevelItem(peak_number)
        if peak_item is not None:
            if channel_number is None:
                spinbox = self.tree.itemWidget(peak_item, 4)
                return spinbox.value()
            else:
                channel_item = peak_item.child(channel_number)
                spinbox = self.tree.itemWidget(channel_item, 4)
                return spinbox.value()
        else:
            return 0


class CircleFitToolbox(Toolbox):
    """
    The Toolbox for the CircleFitWidget.
    
    This Toolbox contains the tools for controlling the circle fit. It has
    two tabs: 'Transfer Function', for tools relating to the construction
    of a transfer function, and 'Autofit Controls', which contains tools 
    for controlling how the circle is fit to the data.
    
    Attributes
    ----------
    sig_autofit_parameter_change : pyqtSignal([bool, str])
      The signal emitted when the set of parameters to automatically adjust in
      the circle fit routine are changed.
      Format (automatically_fit_this_parameter, parameter_name).
    sig_construct_transfer_fn : pyqtSignal
      The signal emitted when a new transfer function is to be constructed.
    sig_show_transfer_fn : pyqtSignal(bool)
      The signal emitted when the visibility of the transfer function is 
      changed. Format (visible).
    """
    
    sig_autofit_parameter_change = pyqtSignal([bool, str])
    sig_construct_transfer_fn = pyqtSignal()
    sig_show_transfer_fn = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        self.init_ui()
    
    def init_ui(self):
        self.init_transfer_function_tab()
        self.init_autofit_tab()
        
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
    
    def init_autofit_tab(self):
        self.autofit_tab = QWidget()
        autofit_layout = QGridLayout()
        
        self.autofit_freq_combobox = QComboBox()
        self.autofit_z_combobox = QComboBox()
        self.autofit_amp_combobox = QComboBox()
        self.autofit_phase_combobox = QComboBox()

        self.autofit_freq_combobox.addItems(["Manual", "Automatic"])
        self.autofit_z_combobox.addItems(["Manual", "Automatic"])
        self.autofit_amp_combobox.addItems(["Manual", "Automatic"])
        self.autofit_phase_combobox.addItems(["Manual", "Automatic"])

        self.autofit_freq_combobox.setCurrentIndex(1)
        self.autofit_z_combobox.setCurrentIndex(1)
        self.autofit_amp_combobox.setCurrentIndex(1)
        self.autofit_phase_combobox.setCurrentIndex(1)

        self.autofit_freq_combobox.currentIndexChanged.connect(self.on_autofit_parameter_change)
        self.autofit_z_combobox.currentIndexChanged.connect(self.on_autofit_parameter_change)
        self.autofit_amp_combobox.currentIndexChanged.connect(self.on_autofit_parameter_change)
        self.autofit_phase_combobox.currentIndexChanged.connect(self.on_autofit_parameter_change)

        self.autofit_reset_btn = QPushButton("Reset")
        self.autofit_reset_btn.clicked.connect(self.reset_to_auto_fit)

        autofit_layout.addWidget(QLabel("Parameters"), 0, 0)
        autofit_layout.addWidget(QLabel("Frequency:"), 1, 0)
        autofit_layout.addWidget(self.autofit_freq_combobox, 1, 1)
        autofit_layout.addWidget(QLabel("Damping ratio:"), 2, 0)
        autofit_layout.addWidget(self.autofit_z_combobox, 2, 1)
        autofit_layout.addWidget(QLabel("Amplitude:"), 3, 0)
        autofit_layout.addWidget(self.autofit_amp_combobox, 3, 1)
        autofit_layout.addWidget(QLabel("Phase:"), 4, 0)
        autofit_layout.addWidget(self.autofit_phase_combobox, 4, 1)
        autofit_layout.addWidget(self.autofit_reset_btn, 5, 1)

        autofit_layout.setColumnStretch(2, 1)
        autofit_layout.setRowStretch(6, 1)

        self.autofit_tab.setLayout(autofit_layout)
        self.addTab(self.autofit_tab, "Autofit controls")
    
    def on_autofit_parameter_change(self, index):
        if self.sender() == self.autofit_freq_combobox:
            self.sig_autofit_parameter_change.emit(index, "frequency")
        elif self.sender() == self.autofit_z_combobox:
            self.sig_autofit_parameter_change.emit(index, "amplitude")
        elif self.sender() == self.autofit_amp_combobox:
            self.sig_autofit_parameter_change.emit(index, "z")
        elif self.sender() == self.autofit_phase_combobox:
            self.sig_autofit_parameter_change.emit(index, "phase")
    
    def reset_to_auto_fit(self):
        """Reset all parameters to 'Automatic'."""
        self.autofit_freq_combobox.setCurrentIndex(1)
        self.autofit_z_combobox.setCurrentIndex(1)
        self.autofit_amp_combobox.setCurrentIndex(1)
        self.autofit_phase_combobox.setCurrentIndex(1)


if __name__ == '__main__':
    CurrentWorkspace = Workspace()
    CurrentWorkspace.configure()
    app = 0

    app = QApplication(sys.argv)
    c = CircleFitWidget()
    c.showMaximized()

    # Create a demo transfer function
    w = np.linspace(0, 25, 3e2)
    d = sdof_modal_peak(w, 5, 0.006, 8e12, np.pi/2) \
        + sdof_modal_peak(w, 10, 0.008, 8e12, 0) \
        + sdof_modal_peak(w, 12, 0.003, 8e12, 0) \
        + sdof_modal_peak(w, 20, 0.01, 22e12, 0)
    v = 1j * w * d
    a = -w**2*d

    #c.transfer_function_type = 'displacement'
    #c.set_data(w, d)

    #c.transfer_function_type = 'velocity'
    #c.set_data(w, v)

    #c.transfer_function_type = 'acceleration'
    #c.set_data(w, a)
    #"""
    cs = ChannelSet()
    
    #c.load_tf(cs)
    import_from_mat("../../tests/transfer_function_clean.mat", cs)
    a = cs.get_channel_data(0, "spectrum")
    c.transfer_function_type = 'acceleration'
    c.set_data(np.linspace(0, cs.get_channel_metadata(0, "sample_rate"), a.size), a)
    #"""
    sys.exit(app.exec_())

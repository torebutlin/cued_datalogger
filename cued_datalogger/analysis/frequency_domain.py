from cued_datalogger.api.pyqtgraph_extensions import InteractivePlotWidget
from cued_datalogger.api.toolbox import Toolbox
from cued_datalogger.api.numpy_extensions import to_dB
from cued_datalogger.api.channel import Channel

from PyQt5.QtWidgets import (QWidget, QGridLayout, QPushButton, QComboBox,
                             QCheckBox, QLabel, QGroupBox)
from PyQt5.QtCore import pyqtSignal

import numpy as np
from numpy.fft import rfft


class FrequencyDomainWidget(InteractivePlotWidget):
    """
    The FrequencyDomainWidget is the main display widget for everything in
    the frequency domain.

    Attributes
    ----------
    channels : list of Channel
        The currently selected channel objects
    current_plot_type : str
        Any of 'linear magnitude', 'log magnitude', 'phase', 'real part',
        'imaginary part', 'nyquist'. The current type of plot that is
        displayed.
    show_coherence : bool
        If `True`, coherence is also plotted on the axes.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.channels = []

        self.plot_types = ['linear magnitude',
                           'log magnitude',
                           'phase',
                           'real part',
                           'imaginary part',
                           'nyquist']
        self.current_plot_type = self.plot_types[0]

        self.plot_transfer_function = False
        self.show_coherence = False

    def set_selected_channels(self, selected_channels):
        """Update which channels are plotted. Sets `self.channels` to
        *selected_channels*."""
        self.channels = []

        if selected_channels:
            self.channels = selected_channels

        self.update_plot(self.plot_transfer_function)

    def set_plot_type(self, plot_type):
        """Set what type of plot is displayed. *plot_type* can be any of
        'linear magnitude', 'log magnitude', 'phase', 'real part', 'imaginary
        part', 'nyquist'."""
        self.current_plot_type = plot_type.lower()
        self.update_plot(self.plot_transfer_function)

    def set_show_coherence(self, show_coherence):
        """Set whether the coherence is displayed."""
        self.show_coherence = show_coherence
        self.update_plot(plot_transfer_function=True)

    def update_plot(self, plot_transfer_function=False):
        """If *plot_transfer_function*, plot the transfer function. Otherwise,
        plot the spectrum."""
        self.plot_transfer_function = plot_transfer_function

        # Clear the plot
        self.clear()

        for channel in self.channels:
            data = None
            # Extract the data
            if self.plot_transfer_function:
                if channel.is_dataset("transfer_function"):
                    data = channel.data("transfer_function")
                else:
                    print("{}: no 'transfer_function' "
                          "dataset.".format(channel.name))
                    continue
            else:
                if channel.is_dataset("spectrum"):
                    data = channel.data("spectrum")
                else:
                    print("{}: no 'spectrum' "
                          "dataset.".format(channel.name))
                    continue

            if data is not None:
                # Plot the data
                if self.current_plot_type == 'linear magnitude':
                    self.plot(channel.data("frequency"),
                              np.abs(data),
                              pen=channel.colour)

                elif self.current_plot_type == 'log magnitude':
                    self.plot(channel.data("frequency"),
                              to_dB(np.abs(data)),
                              pen=channel.colour)

                elif self.current_plot_type == 'phase':
                    self.plot(channel.data("frequency"),
                              np.angle(data, deg=True),
                              pen=channel.colour)

                elif self.current_plot_type == 'real part':
                    self.plot(channel.data("frequency"),
                              np.real(data),
                              pen=channel.colour)

                elif self.current_plot_type == 'imaginary part':
                    self.plot(channel.data("frequency"),
                              np.imag(data),
                              pen=channel.colour)

                elif self.current_plot_type == 'nyquist':
                    self.plot(np.real(data),
                              np.imag(data),
                              pen=channel.colour)

            if self.plot_transfer_function and self.show_coherence:
                print("Plotting coherence...")
                if channel.is_dataset("coherence"):
                    if self.current_plot_type == 'linear magnitude':
                        self.plot(channel.data("frequency"),
                                  np.abs(channel.data("coherence")))
                    elif self.current_plot_type == 'log magnitude':
                        self.plot(channel.data("frequency"),
                                  to_dB(np.abs(channel.data("coherence"))))
                    elif self.current_plot_type == 'phase':
                        self.plot(channel.data("frequency"),
                                  np.angle(channel.data("coherence"), deg=True))
                    elif self.current_plot_type == 'real part':
                        self.plot(channel.data("frequency"),
                                  channel.data("coherence").real)
                    elif self.current_plot_type == 'imaginary part':
                        self.plot(channel.data("frequency"),
                                  channel.data("coherence").imag)
                    elif self.current_plot_type == 'nyquist':
                        self.plot(channel.data("coherence").real,
                                  channel.data("coherence").imag)
                    print("Done.")
                else:
                    print("{}: no 'coherence' dataset".format(channel.name))

    def calculate_spectrum(self):
        """Calculate the frequency spectrum of all the selected channels."""
        print("Calculating spectrum...")
        for channel in self.channels:
            if channel.is_dataset("time_series"):
                time_series = channel.data("time_series")
                window = np.hanning(time_series.size)
                spectrum = rfft(time_series * window)

                channel.add_dataset("spectrum", data=spectrum)

            else:
                print("Skipping {}: no 'time_series' "
                      "dataset.".format(channel.name))
                continue
        print("Done.")
        self.update_plot()

    def calculate_transfer_function(self, input_channel=None):
        """Calculate the transfer function, using the channel object given by
        *input_channel* as the input. If no channel specified, treat the first
        selected channel as input."""
        print("Calculating transfer function...")

        if not input_channel:
            input_channel = self.channels[0]
        if not isinstance(input_channel, Channel):
            print("Error in calculating transfer function: no input channel.")
            pass

        print("Calculating transfer function...")

        input_spectrum = input_channel.data("spectrum")
        input_auto_spectrum = calculate_auto_spectrum(input_spectrum)

        for channel in self.channels:
            # Skip the input channel
            if channel == input_channel:
                pass

            if channel.is_dataset("spectrum"):
                # Get the data
                output_spectrum = channel.data("spectrum")

                # Calculate the auto- and cross- spectra
                output_auto_spectrum = \
                    calculate_auto_spectrum(output_spectrum)

                cross_spectrum = \
                    calculate_cross_spectrum(input_spectrum,
                                                  output_spectrum)

                # Calculate the transfer function
                transfer_function = output_auto_spectrum / cross_spectrum
                # Update the channel
                channel.add_dataset("transfer_function", data=transfer_function)

                # Calculate the coherence
                coherence = (cross_spectrum * cross_spectrum.conj() /
                             input_auto_spectrum * output_auto_spectrum).real
                channel.add_dataset("coherence", data=coherence)

            else:
                print("Skipping {}: no 'spectrum' "
                      "dataset.".format(channel.name))
                continue
        print("Done.")
        self.update_plot(plot_transfer_function=True)


def calculate_auto_spectrum(spectrum):
    return spectrum * spectrum.conj()

def calculate_cross_spectrum(input_spectrum, output_spectrum):
    return input_spectrum.conj() * output_spectrum

def compute_transfer_function(autospec_in,autospec_out,crossspec):
    transfer_func = (autospec_out/crossspec)
    coherence = ((crossspec * np.conjugate(crossspec))/(autospec_in*autospec_out))
    return(transfer_func,np.real(coherence))


class FrequencyToolbox(Toolbox):
    """Toolbox containing the Frequency Domain controls."""
    sig_convert_to_circle_fit = pyqtSignal()
    sig_plot_type_changed = pyqtSignal(str)
    sig_plot_transfer_function = pyqtSignal()
    sig_plot_frequency_spectrum = pyqtSignal()
    sig_show_coherence = pyqtSignal(bool)
    sig_calculate_transfer_function = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.parent = parent

        self.init_ui()

    def init_ui(self):
        # # Plot options tab
        self.plot_options_tab = QWidget(self)
        plot_options_tab_layout = QGridLayout()

        plot_options_tab_layout.addWidget(QLabel("Plot:"), 0, 0)
        self.current_plot_combobox = QComboBox(self)
        self.current_plot_combobox.addItems(['Frequency spectrum', 'Transfer function'])
        self.current_plot_combobox.setCurrentIndex(0)
        self.current_plot_combobox.currentIndexChanged[str].connect(self.on_current_plot_changed)
        plot_options_tab_layout.addWidget(self.current_plot_combobox, 1, 0)

        self.show_coherence_checkbox = QCheckBox('Show coherence',self)
        self.show_coherence_checkbox.stateChanged.connect(self.sig_show_coherence.emit)
        self.show_coherence_checkbox.stateChanged.connect(self.set_plot_transfer_function)
        plot_options_tab_layout.addWidget(self.show_coherence_checkbox, 2, 0)

        plot_options_tab_layout.addWidget(QLabel("Plot type:"), 3, 0)
        self.plot_type_combobox = QComboBox(self.plot_options_tab)
        self.plot_type_combobox.addItems(['Linear Magnitude',
                                          'Log Magnitude',
                                          'Phase',
                                          'Real Part',
                                          'Imaginary Part',
                                          'Nyquist'])
        self.plot_type_combobox.setCurrentIndex(0)
        self.plot_type_combobox.currentIndexChanged[str].connect(self.sig_plot_type_changed.emit)
        plot_options_tab_layout.addWidget(self.plot_type_combobox, 4, 0)

        plot_options_tab_layout.setRowStretch(5, 1)
        self.plot_options_tab.setLayout(plot_options_tab_layout)

        self.addTab(self.plot_options_tab, "Plot Options")

        # # Conversion tab
        self.convert_tab = QWidget(self)
        convert_tab_layout = QGridLayout()

        transfer_function_groupbox = QGroupBox("Transfer function")
        transfer_function_groupbox_layout = QGridLayout()

        label = QLabel("Use first selected channel as input to compute "
                       "transfer function")
        label.setWordWrap(True)
        transfer_function_groupbox_layout.addWidget(label, 0, 0)
        self.convert_to_transfer_function_button = \
            QPushButton("Compute transfer function")
        self.convert_to_transfer_function_button.clicked.connect(self.sig_calculate_transfer_function.emit)
        self.convert_to_transfer_function_button.clicked.connect(self.set_plot_transfer_function)
        transfer_function_groupbox_layout.addWidget(self.convert_to_transfer_function_button, 1, 0)

        transfer_function_groupbox.setLayout(transfer_function_groupbox_layout)
        convert_tab_layout.addWidget(transfer_function_groupbox, 0, 0)

        modal_fitting_groupbox = QGroupBox("Modal fitting")
        modal_fitting_groupbox_layout = QGridLayout()

        self.circle_fit_btn = QPushButton("Circle fit")
        self.circle_fit_btn.clicked.connect(self.sig_convert_to_circle_fit.emit)
        modal_fitting_groupbox_layout.addWidget(self.circle_fit_btn, 1, 0)

        modal_fitting_groupbox.setLayout(modal_fitting_groupbox_layout)
        convert_tab_layout.addWidget(modal_fitting_groupbox, 1, 0)

        convert_tab_layout.setRowStretch(2, 1)
        self.convert_tab.setLayout(convert_tab_layout)

        self.addTab(self.convert_tab, "Conversion")

    def set_plot_transfer_function(self):
        print("Plotting transfer function...")
        self.current_plot_combobox.setCurrentIndex(1)

    def set_plot_spectrum(self):
        print("Plotting spectrum...")
        self.current_plot_combobox.setCurrentIndex(0)

    def on_current_plot_changed(self, current_plot):
        if current_plot == 'Frequency spectrum':
            self.sig_plot_frequency_spectrum.emit()
        elif current_plot == 'Transfer function':
            self.sig_plot_transfer_function.emit()

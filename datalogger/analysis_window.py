import numpy as np
from numpy.fft import rfft,fft

from PyQt5.QtWidgets import (QWidget, QApplication, QTabWidget, QComboBox,
                             QHBoxLayout, QMainWindow, QPushButton,
                             QVBoxLayout, QAction, QMenu)

import sys

#from datalogger.analysis.circle_fit import CircleFitWidget, CircleFitToolbox
from datalogger.analysis.circle_fit_v2 import CircleFitWidget, CircleFitToolbox
from datalogger.analysis.frequency_domain import FrequencyDomainWidget, FrequencyToolbox
from datalogger.analysis.sonogram import SonogramDisplayWidget, SonogramToolbox
from datalogger.analysis.time_domain import TimeDomainWidget, TimeToolbox

from datalogger.api.addons import AddonManager
from datalogger.api.channel import ChannelSet, ChannelSelectWidget, ChannelMetadataWidget
from datalogger.api.file_import import DataImportWidget
from datalogger.api.toolbox import Toolbox, MasterToolbox

import datalogger.acquisition_window as lpUI
from datalogger.acquisition.RecordingUIs import DevConfigUI


class AnalysisDisplayTabWidget(QTabWidget):
    """The central widget for display in the analysis window"""
    def __init__(self, *arg, **kwarg):
        super().__init__(*arg, **kwarg)

        self.init_ui()

    def init_ui(self):
        self.setMovable(False)
        self.setTabsClosable(False)

        self.timedomain_widget = TimeDomainWidget(self)

        self.freqdomain_widget = FrequencyDomainWidget(self)
        self.sonogram_widget = SonogramDisplayWidget(self)
        self.circle_widget = CircleFitWidget(self)

        # Create the tabs
        self.addTab(self.timedomain_widget, "Time Domain")
        self.addTab(self.freqdomain_widget, "Frequency Domain")
        self.addTab(self.sonogram_widget, "Sonogram")
        self.addTab(self.circle_widget, "Circle Fit")


class ProjectMenu(QMenu):
    def __init__(self,parent):
        super().__init__('Project',parent)
        self.parent = parent
        self.initMenu()

    def initMenu(self):
        newAct = QAction('&New', self)
        newAct.setShortcut('Ctrl+N')

        setAct = QAction('&Settings', self)

        exitAct = QAction('&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')

        self.addActions([newAct,setAct,exitAct])


class AnalysisWindow(QMainWindow):
    """
    Data Analysis Window
    """
    def __init__(self):
        super().__init__()

        self.setGeometry(500,300,800,500)
        self.setWindowTitle('AnalysisWindow')

        #self.new_cs = ChannelSet()
        self.create_test_channelset()
        self.init_ui()

        self.setFocus()
        self.show()

    def init_toolbox(self):
        """Create the master toolbox"""
        self.toolbox = MasterToolbox(self)

        # # Time toolbox
        self.time_toolbox = TimeToolbox(self.toolbox)
        self.time_toolbox.sig_converted_FFT.connect(self.plot_fft)
        self.time_toolbox.sig_convert_to_sonogram.connect(self.plot_sonogram)

        # # Frequency toolbox
        self.frequency_toolbox = FrequencyToolbox(self.toolbox)
        self.frequency_toolbox.set_channel_set(self.cs)
        self.frequency_toolbox.sig_plot_type_changed.connect(self.display_tabwidget.freqdomain_widget.set_plot_type)
        self.frequency_toolbox.sig_view_type_changed.connect(self.switch_freq_plot)
        self.frequency_toolbox.sig_converted_TF.connect(self.plot_tf)
        self.frequency_toolbox.sig_coherence_plot.connect(self.display_tabwidget.freqdomain_widget.switch_cor_plot)
        self.frequency_toolbox.sig_convert_to_circle_fit.connect(self.circle_fitting)

        # # Sonogram toolbox
        self.sonogram_toolbox = SonogramToolbox(self.toolbox)
        self.sonogram_toolbox.sig_contour_spacing_changed.connect(self.display_tabwidget.sonogram_widget.update_contour_spacing)
        self.sonogram_toolbox.sig_num_contours_changed.connect(self.display_tabwidget.sonogram_widget.update_num_contours)
        self.sonogram_toolbox.sig_window_overlap_fraction_changed.connect(self.display_tabwidget.sonogram_widget.update_window_overlap_fraction)
        self.sonogram_toolbox.sig_window_width_changed.connect(self.display_tabwidget.sonogram_widget.update_window_width)

        # # Circle Fit toolbox
        self.circle_fit_toolbox = CircleFitToolbox(self.toolbox)
        self.circle_fit_toolbox.sig_show_transfer_fn.connect(self.display_tabwidget.circle_widget.show_transfer_fn)
        self.circle_fit_toolbox.sig_construct_transfer_fn.connect(self.display_tabwidget.circle_widget.construct_transfer_fn)
        #self.circle_fit_toolbox.sig_autofit_parameter_change.connect(self.display_tabwidget.circle_widget.update_autofit_parameters)

        self.toolbox.add_toolbox(self.time_toolbox)
        self.toolbox.add_toolbox(self.frequency_toolbox)
        self.toolbox.add_toolbox(self.sonogram_toolbox)
        self.toolbox.add_toolbox(self.circle_fit_toolbox)
        self.toolbox.set_toolbox(0)

    def init_global_toolbox(self):
        self.global_toolbox = MasterToolbox()

        self.global_tools = Toolbox('right', self.global_toolbox)

        # # Acquisition Window
        self.liveplot = None
        dev_configUI = DevConfigUI()
        dev_configUI.config_button.setText('Open Oscilloscope')
        dev_configUI.config_button.clicked.connect(self.open_liveplot)
        self.global_tools.addTab(dev_configUI,'Oscilloscope')

        # # Channel Selection
        self.channel_select_widget = ChannelSelectWidget(self.global_tools)
        self.channel_select_widget.sig_channel_selection_changed.connect(self.display_tabwidget.timedomain_widget.set_selected_channels)
        self.channel_select_widget.sig_channel_selection_changed.connect(self.display_tabwidget.freqdomain_widget.set_selected_channels)
        self.channel_select_widget.sig_channel_selection_changed.connect(self.display_tabwidget.sonogram_widget.set_selected_channels)
        self.channel_select_widget.sig_channel_selection_changed.connect(self.sonogram_toolbox.set_selected_channels)
        self.channel_select_widget.sig_channel_selection_changed.connect(self.display_tabwidget.circle_widget.set_selected_channels)

        self.global_tools.addTab(self.channel_select_widget, 'Channel Selection')

        # # Channel Metadata
        self.channel_metadata_widget = ChannelMetadataWidget(self.global_tools)
        self.global_tools.addTab(self.channel_metadata_widget, 'Channel Metadata')

        self.channel_metadata_widget.metadataChange.connect(self.update_cs)

        # # Addon Manager
        self.addon_widget = AddonManager(self)
        self.global_tools.addTab(self.addon_widget, 'Addon Manager')

        # # Import
        self.import_widget = DataImportWidget(self)
        self.import_widget.add_data_btn.clicked.connect(lambda: self.add_import_data('Extend'))
        self.import_widget.rep_data_btn.clicked.connect(lambda: self.add_import_data('Replace'))
        self.global_tools.addTab(self.import_widget, 'Import Files')

        self.global_toolbox.add_toolbox(self.global_tools)

    def update_cs(self, cs):
        self.cs = cs
        self.channel_select_widget.cs = self.cs
        self.channel_select_widget.set_channel_name()

    def init_ui(self):
        menubar = self.menuBar()
        menubar.addMenu(ProjectMenu(self))

        # # Create the main widget
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        # Create the analysis tools tab widget
        self.display_tabwidget = AnalysisDisplayTabWidget(self)

        # Create the toolbox
        self.init_toolbox()
        self.display_tabwidget.currentChanged.connect(self.toolbox.set_toolbox)

        # Create the global toolbox
        self.init_global_toolbox()

        self.tfplots = []
        self.config_channelset()
        self.plot_time_series()
        #self.plot_fft()
        self.display_tabwidget.setCurrentWidget(self.display_tabwidget.timedomain_widget)

        # Add the widgets
        self.main_layout.addWidget(self.toolbox)
        self.main_layout.addWidget(self.display_tabwidget)
        self.main_layout.addWidget(self.global_toolbox)
        # Set the stretch factors
        self.main_layout.setStretchFactor(self.toolbox, 0)
        self.main_layout.setStretchFactor(self.display_tabwidget, 1)
        self.main_layout.setStretchFactor(self.global_toolbox, 0.5)

    def create_test_channelset(self):
        self.cs = ChannelSet(5)
        t = np.arange(1000)/44100
        for i, channel in enumerate(self.cs.channels):
            self.cs.add_channel_dataset(i, 'time_series', np.sin(t*2*np.pi*100*(i+1)))
            self.cs.add_channel_dataset(i,'spectrum', [])

        self.cs.add_channel_dataset(i,'time_series', np.sin(t*2*np.pi*100*(i+1))*np.exp(-t/t[-1]) )
        self.cs.add_channel_dataset(i,'spectrum', [])

    def open_liveplot(self):
        if not self.liveplot:
            self.liveplot = lpUI.LiveplotApp(self)
            self.liveplot.done.connect(self.done_liveplot)
            self.liveplot.dataSaved.connect(self.receive_data)
            self.liveplot.show()

    def receive_data(self,tab_num = 0):
        self.config_channelset()
        self.plot_time_series()
        self.plot_fft()

        self.display_tabwidget.setCurrentIndex(tab_num)
        if tab_num == 1:
            self.switch_freq_plot('Transfer Function')

    def done_liveplot(self):
        self.liveplot.done.disconnect()
        self.liveplot = None

    def config_channelset(self):
        self.channel_select_widget.set_channel_set(self.cs)
        self.channel_metadata_widget.set_channel_set(self.cs)
        self.time_toolbox.set_channel_set(self.cs)
        self.frequency_toolbox.set_channel_set(self.cs)

    def plot_time_series(self):
        self.display_tabwidget.setCurrentWidget(self.display_tabwidget.timedomain_widget)
        self.display_tabwidget.timedomain_widget.set_selected_channels(self.cs.channels)

    def switch_freq_plot(self,dtype):
        if dtype == 'Fourier Transform':
            self.plot_fft()
        elif dtype == 'Transfer Function':
            self.plot_tf()

    def plot_fft(self):
        # Switch to frequency domain tab
        self.display_tabwidget.setCurrentWidget(self.display_tabwidget.freqdomain_widget)
        self.display_tabwidget.freqdomain_widget.set_view_type("spectrum")
        self.display_tabwidget.freqdomain_widget.set_selected_channels(self.channel_select_widget.selected_channels())
        self.frequency_toolbox.set_view_type('Fourier Transform')

    def plot_tf(self):
        #TODO: calculate TF function if none is found
        self.display_tabwidget.setCurrentWidget(self.display_tabwidget.freqdomain_widget)
        self.display_tabwidget.freqdomain_widget.set_view_type("TF")
        self.display_tabwidget.freqdomain_widget.set_selected_channels(self.channel_select_widget.selected_channels())
        self.frequency_toolbox.set_view_type('Transfer Function')


    def plot_sonogram(self):
        self.display_tabwidget.setCurrentWidget(self.display_tabwidget.sonogram_widget)
        self.display_tabwidget.sonogram_widget.set_selected_channels(self.cs.channels)


    def circle_fitting(self):
        self.display_tabwidget.setCurrentWidget(self.display_tabwidget.circle_widget)
        self.display_tabwidget.circle_widget.set_selected_channels(self.cs.channels)
        """
        # Send the first available Transfer Function
        for i in range(len(self.cs)):
            fdata = self.cs.get_channel_data(i, "TF")
            if not fdata.shape[0] == 0:
                self.display_tabwidget.circle_widget.transfer_function_type = 'acceleration'
                self.display_tabwidget.circle_widget.set_data(
                        np.linspace(0, self.cs.get_channel_metadata(i, "sample_rate"),fdata.size),
                        fdata)

        print('No Transfer Function Available')
        """

    def add_import_data(self,mode):
        if mode == 'Extend':
            self.cs.channels.extend(self.import_widget.new_cs.channels)
        elif mode == 'Replace':
            self.cs = self.import_widget.new_cs

        self.receive_data()
        self.import_widget.clear()


if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()
    w.show()

    sys.exit(app.exec_())

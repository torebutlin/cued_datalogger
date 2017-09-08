import numpy as np
from numpy.fft import rfft,fft

from PyQt5.QtWidgets import (QWidget, QApplication, QTabWidget, QComboBox,
                             QHBoxLayout, QMainWindow, QPushButton,
                             QVBoxLayout, QAction, QMenu)

import sys

from cued_datalogger.analysis.circle_fit import CircleFitWidget, CircleFitToolbox
from cued_datalogger.analysis.frequency_domain import FrequencyDomainWidget, FrequencyToolbox
from cued_datalogger.analysis.sonogram import SonogramDisplayWidget, SonogramToolbox
from cued_datalogger.analysis.time_domain import TimeDomainWidget, TimeToolbox

from cued_datalogger.api.addons import AddonManager
from cued_datalogger.api.channel import ChannelSet, ChannelSelectWidget, ChannelMetadataWidget
from cued_datalogger.api.file_import import DataImportWidget
from cued_datalogger.api.file_export import DataExportWidget
from cued_datalogger.api.toolbox import Toolbox, MasterToolbox

from cued_datalogger.acquisition.acquisition_window import AcquisitionWindow
from cued_datalogger.acquisition.RecordingUIs import DevConfigUI

class AnalysisDisplayTabWidget(QTabWidget):
    """This is the central widget for the AnalysisWindow, where graphs, data,
    and results are displayed. In general the user does not interact explicitly
    with this widget, instead accessing the widgets it contains.

    Attributes
    ----------
    circle_widget : :class:`~cued_datalogger.analysis.circle_fit.CircleFitWidget`
    freqdomain_widget : :class:`~cued_datalogger.analysis.frequency_domain.FrequencyDomainWidget`
    sonogram_widget : :class:`~cued_datalogger.analysis.sonogram.SonogramDisplayWidget`
    timedomain_widget : :class:`~cued_datalogger.analysis.time_domain.TimeDomainWidget`
    """
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
    '''
    A simple drop-down menu for demonstration purposes.
    Currently does not do anything.
    '''
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
    The main window for analysing and processing data.

    Attributes
    ----------
    cs : :class:`~cued_datalogger.api.channel.ChannelSet`
      The ChannelSet containing all the data. Data is accessed through this
      ChannelSet.

    menubar : :class:`PyQt5.QtWidgets.QMenuBar`

    toolbox : :class:`~cued_datalogger.api.toolbox.MasterToolbox`
      The widget containing local tools and operations. Contains four
      toolboxes: :attr:`time_toolbox`, :attr:`frequency_toolbox`,
      :attr:`sonogram_toolbox`, :attr:`circle_fit_toolbox`.

    time_toolbox : :class:`~cued_datalogger.analysis.time_domain.TimeToolbox`
    frequency_toolbox : :class:`~cued_datalogger.analysis.frequency_domain.FrequencyToolbox`
    sonogram_toolbox : :class:`~cued_datalogger.analysis.sonogram.SonogramToolbox`
    circle_fit_toolbox : :class:`~cued_datalogger.analysis.circle_fit.CircleFitToolbox`

    display_tabwidget : :class:`~cued_datalogger.analysis_window.AnalysisDisplayTabWidget`
        The central widget for display.

    global_master_toolbox : :class:`~cued_datalogger.api.toolbox.MasterToolbox`
      The master toolbox containing the :attr:`global_toolbox`.

    global_toolbox : :class:`~cued_datalogger.api.toolbox.Toolbox`
      The widget containing global tools and operations. Has five tabs,
      containing: <acquisition window launcher>, :attr:`channel_select_widget`,
      :attr:`channel_metadata_widget`, :attr:`addon_widget`,
      :attr:`import_widget`.
    acquisition_window : :class:`~cued_datalogger.acquisition_window.AcquisitionWindow`
    channel_select_widget : :class:`~cued_datalogger.api.channel.ChannelSelectWidget`
    channel_metadata_widget : :class:`~cued_datalogger.api.channel.ChannelMetadataWidget`
    addon_widget : :class:`~cued_datalogger.api.addons.AddonManager`
    import_widget : :class:`~cued_datalogger.api.file_import.DataImportWidget`
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
        self.frequency_toolbox.sig_view_type_changed.connect(self.set_freq_plot_type)
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

    def init_global_master_toolbox(self):
        self.global_master_toolbox = MasterToolbox()

        self.global_toolbox = Toolbox('right', self.global_master_toolbox)

        # # Acquisition Window
        self.acquisition_window = None
        self.dev_configUI = DevConfigUI()
        self.dev_configUI.config_button.setText('Open AcquisitionWindow')
        self.dev_configUI.config_button.clicked.connect(self.open_acquisition_window)
        self.global_toolbox.addTab(self.dev_configUI,'AcquisitionWindow')

        # # Channel Selection
        self.channel_select_widget = ChannelSelectWidget(self.global_toolbox)
        self.channel_select_widget.sig_channel_selection_changed.connect(self.display_tabwidget.timedomain_widget.set_selected_channels)
        self.channel_select_widget.sig_channel_selection_changed.connect(self.display_tabwidget.freqdomain_widget.set_selected_channels)
        self.channel_select_widget.sig_channel_selection_changed.connect(self.display_tabwidget.sonogram_widget.set_selected_channels)
        self.channel_select_widget.sig_channel_selection_changed.connect(self.sonogram_toolbox.set_selected_channels)
        self.channel_select_widget.sig_channel_selection_changed.connect(self.display_tabwidget.circle_widget.set_selected_channels)

        self.global_toolbox.addTab(self.channel_select_widget, 'Channel Selection')

        # # Channel Metadata
        self.channel_metadata_widget = ChannelMetadataWidget(self.global_toolbox)
        self.global_toolbox.addTab(self.channel_metadata_widget, 'Channel Metadata')

        self.channel_metadata_widget.metadataChange.connect(self.update_cs)

        # # Addon Manager
        self.addon_widget = AddonManager(self)
        self.global_toolbox.addTab(self.addon_widget, 'Addon Manager')

        # # Import
        self.import_widget = DataImportWidget(self)
        self.import_widget.add_data_btn.clicked.connect(lambda: self.add_import_data('Extend'))
        self.import_widget.rep_data_btn.clicked.connect(lambda: self.add_import_data('Replace'))
        self.global_toolbox.addTab(self.import_widget, 'Import Files')

        # # Export
        self.export_widget = DataExportWidget(self)
        self.global_toolbox.addTab(self.export_widget, 'Export Files')

        self.global_master_toolbox.add_toolbox(self.global_toolbox)

    def update_cs(self, cs):
        self.cs = cs
        self.channel_select_widget.cs = self.cs
        self.channel_select_widget.set_channel_name()

    def init_ui(self):
        # Add the drop-down menu
        self.menubar = self.menuBar()
        self.menubar.addMenu(ProjectMenu(self))

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
        self.init_global_master_toolbox()

        self.tfplots = []
        self.configure_channelset()
        self.plot_time_series()
        #self.plot_fft()
        self.display_tabwidget.setCurrentWidget(self.display_tabwidget.timedomain_widget)

        # Add the widgets
        self.main_layout.addWidget(self.toolbox)
        self.main_layout.addWidget(self.display_tabwidget)
        self.main_layout.addWidget(self.global_master_toolbox)
        # Set the stretch factors
        self.main_layout.setStretchFactor(self.toolbox, 0)
        self.main_layout.setStretchFactor(self.display_tabwidget, 1)
        self.main_layout.setStretchFactor(self.global_master_toolbox, 0.5)

    def create_test_channelset(self):
        self.cs = ChannelSet(5)
        t = np.arange(0,0.5,1/5000)
        for i, channel in enumerate(self.cs.channels):
            self.cs.set_channel_metadata(i,{'sample_rate': 5000})
            self.cs.add_channel_dataset(i, 'time_series', np.sin(t*2*np.pi*100*(i+1)))
            self.cs.add_channel_dataset(i,'spectrum', [])
            channel.name = "Channel {}".format(i)
        self.cs.add_channel_dataset(i,'time_series', np.sin(t*2*np.pi*100*(i+1))*np.exp(-t/t[-1]) )
        self.cs.add_channel_dataset(i,'spectrum', [])

    def open_acquisition_window(self):
        if not self.acquisition_window:
            recType, configs = self.dev_configUI.read_device_config()
            if not any([c==None for c in configs]):
                self.acquisition_window = AcquisitionWindow(self, recType, configs)
            else:
                self.acquisition_window = AcquisitionWindow(self)
            self.acquisition_window.done.connect(self.done_acquisition_window)
            self.acquisition_window.dataSaved.connect(self.receive_data)
            self.acquisition_window.show()

    def receive_data(self, tab_number=0):
        self.configure_channelset()
        self.plot_time_series(switch_to_tab=False)
        self.plot_fft(switch_to_tab=False)
        self.plot_sonogram(switch_to_tab=False)
        self.circle_fitting(switch_to_tab=False)

        if self.sender() == self.acquisition_window:
            self.display_tabwidget.setCurrentIndex(tab_number)
            if tab_number == 1:
                self.set_freq_plot_type('Transfer Function')

    def done_acquisition_window(self):
        self.acquisition_window.done.disconnect()
        self.acquisition_window = None

    def configure_channelset(self):
        self.channel_select_widget.set_channel_set(self.cs)
        self.channel_metadata_widget.set_channel_set(self.cs)
        self.time_toolbox.set_channel_set(self.cs)
        self.frequency_toolbox.set_channel_set(self.cs)
        self.export_widget.set_channel_set(self.cs)

    def plot_time_series(self, switch_to_tab=True):
        if switch_to_tab:
            self.display_tabwidget.setCurrentWidget(self.display_tabwidget.timedomain_widget)
        self.display_tabwidget.timedomain_widget.set_selected_channels(self.cs.channels)

    def set_freq_plot_type(self, plot_type):
        if plot_type == 'Fourier Transform':
            self.plot_fft()
        elif plot_type == 'Transfer Function':
            self.plot_tf()

    def plot_fft(self, switch_to_tab=True):
        if switch_to_tab:
            # Switch to frequency domain tab
            self.display_tabwidget.setCurrentWidget(self.display_tabwidget.freqdomain_widget)
        self.display_tabwidget.freqdomain_widget.set_view_type("spectrum")
        self.display_tabwidget.freqdomain_widget.set_selected_channels(self.cs.channels)
        self.frequency_toolbox.set_view_type('Fourier Transform')

    def plot_tf(self, switch_to_tab=True):
        if switch_to_tab:
            self.display_tabwidget.setCurrentWidget(self.display_tabwidget.freqdomain_widget)
        #TODO: calculate TF function if none is found
        self.display_tabwidget.freqdomain_widget.set_view_type("TF")
        self.display_tabwidget.freqdomain_widget.set_selected_channels(self.cs.channels)
        self.frequency_toolbox.set_view_type('Transfer Function')

    def plot_sonogram(self, switch_to_tab=True):
        if switch_to_tab:
            self.display_tabwidget.setCurrentWidget(self.display_tabwidget.sonogram_widget)
        self.display_tabwidget.sonogram_widget.set_selected_channels(self.cs.channels)

    def circle_fitting(self, switch_to_tab=True):
        if switch_to_tab:
            self.display_tabwidget.setCurrentWidget(self.display_tabwidget.circle_widget)
        self.display_tabwidget.circle_widget.set_selected_channels(self.cs.channels)

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

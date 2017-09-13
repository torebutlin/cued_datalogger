import numpy as np
from numpy.fft import rfft,fft

from PyQt5.QtWidgets import (QWidget, QApplication, QTabWidget, QComboBox,
                             QHBoxLayout, QMainWindow, QPushButton,
                             QVBoxLayout, QAction, QMenu, QSplitter)
from PyQt5.Qt import QSizePolicy

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

    freqdomain_widget : :class`~cued_datalogger.analysis.frequency_domain.FrequencyDomainWidget`
    sonogram_widget : :class:`~cued_datalogger.analysis.sonogram.SonogramDisplayWidget`
    circle_widget : :class:`~cued_datalogger.analysis.circle_fit.CircleFitWidget`

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

        self.setWindowTitle('AnalysisWindow')

        self.create_test_channelset()
        self._init_ui()

        self.setFocus()
        self.showMaximized()

    def _init_ui(self):
        # Add the drop-down menu
        self.menubar = self.menuBar()
        self.menubar.addMenu(ProjectMenu(self))

        # # Create the main widget
        self.splitter = QSplitter(self)
        self.splitter.setHandleWidth(5)
        self.splitter.setChildrenCollapsible(False)
        self.setCentralWidget(self.splitter)

        # Create the analysis tools tab widget
        self._init_display_tabwidget()

        # Create the toolbox
        self._init_toolbox()
        self.display_tabwidget.currentChanged.connect(self.toolbox.set_toolbox)
        self.display_tabwidget.setSizePolicy(QSizePolicy.Expanding,
                                             QSizePolicy.Expanding)

        # Create the global toolbox
        self._init_global_master_toolbox()

        # Configure
        self.update_channelset()
        self.goto_time_series()

        # Add the widgets
        self.splitter.addWidget(self.toolbox)
        self.splitter.addWidget(self.display_tabwidget)
        self.splitter.addWidget(self.global_master_toolbox)

    def _init_display_tabwidget(self):
        """Create the display tabwidget."""
        self.display_tabwidget = QTabWidget(self)
        self.timedomain_widget = TimeDomainWidget()
        self.freqdomain_widget = FrequencyDomainWidget()
        self.sonogram_widget = SonogramDisplayWidget()
        self.circle_widget = CircleFitWidget()

        # Create the tabs
        self.display_tabwidget.addTab(self.timedomain_widget, "Time Domain")
        self.display_tabwidget.addTab(self.freqdomain_widget, "Frequency Domain")
        self.display_tabwidget.addTab(self.sonogram_widget, "Sonogram")
        self.display_tabwidget.addTab(self.circle_widget, "Circle Fit")

    def _init_toolbox(self):
        """Create the master toolbox"""
        self.toolbox = MasterToolbox(self)
        self.toolbox.sig_collapsed_changed.connect(self._update_splitter)

        # # Time toolbox
        self.time_toolbox = TimeToolbox(self.toolbox)
        self.time_toolbox.sig_convert_to_fft.connect(self.goto_frequency_spectrum)
        self.time_toolbox.sig_convert_to_sonogram.connect(self.goto_sonogram)

        # # Frequency toolbox
        self.frequency_toolbox = FrequencyToolbox(self.toolbox)
        self.frequency_toolbox.sig_calculate_transfer_function.connect(self.freqdomain_widget.calculate_transfer_function)
        self.frequency_toolbox.sig_convert_to_circle_fit.connect(self.goto_circle_fit)
        self.frequency_toolbox.sig_plot_frequency_spectrum.connect(lambda: self.freqdomain_widget.update_plot(False))
        self.frequency_toolbox.sig_plot_transfer_function.connect(lambda: self.freqdomain_widget.update_plot(True))
        self.frequency_toolbox.sig_plot_type_changed.connect(self.freqdomain_widget.set_plot_type)
        self.frequency_toolbox.sig_show_coherence.connect(self.freqdomain_widget.set_show_coherence)

        # # Sonogram toolbox
        self.sonogram_toolbox = SonogramToolbox(self.toolbox)
        self.sonogram_toolbox.sig_contour_spacing_changed.connect(self.sonogram_widget.update_contour_spacing)
        self.sonogram_toolbox.sig_num_contours_changed.connect(self.sonogram_widget.update_num_contours)
        self.sonogram_toolbox.sig_window_overlap_fraction_changed.connect(self.sonogram_widget.update_window_overlap_fraction)
        self.sonogram_toolbox.sig_window_width_changed.connect(self.sonogram_widget.update_window_width)

        # # Circle Fit toolbox
        self.circle_fit_toolbox = CircleFitToolbox(self.toolbox)
        self.circle_fit_toolbox.sig_show_transfer_fn.connect(self.circle_widget.show_transfer_fn)
        self.circle_fit_toolbox.sig_construct_transfer_fn.connect(self.circle_widget.construct_transfer_fn)

        self.toolbox.add_toolbox(self.time_toolbox)
        self.toolbox.add_toolbox(self.frequency_toolbox)
        self.toolbox.add_toolbox(self.sonogram_toolbox)
        self.toolbox.add_toolbox(self.circle_fit_toolbox)
        self.toolbox.set_toolbox(0)

    def _init_global_master_toolbox(self):
        self.global_master_toolbox = MasterToolbox()
        self.global_master_toolbox.sig_collapsed_changed.connect(self._update_splitter)

        self.global_toolbox = Toolbox('right', self.global_master_toolbox)

        # # Acquisition Window
        self.acquisition_window = None
        self.device_config = DevConfigUI()
        self.device_config.config_button.setText('Open AcquisitionWindow')
        self.device_config.config_button.clicked.connect(self.open_acquisition_window)
        self.global_toolbox.addTab(self.device_config, 'Acquisition Window')

        # # Channel Selection
        self.channel_select_widget = ChannelSelectWidget(self.global_toolbox)
        self.channel_select_widget.sig_channel_selection_changed.connect(self.set_selected_channels)
        self.global_toolbox.addTab(self.channel_select_widget, 'Channel Selection')

        # # Channel Metadata
        self.channel_metadata_widget = ChannelMetadataWidget(self.global_toolbox)
        self.global_toolbox.addTab(self.channel_metadata_widget, 'Channel Metadata')

        self.channel_metadata_widget.metadataChange.connect(self.update_channelset)

        # # Addon Manager
        self.addon_widget = AddonManager(self)
        self.global_toolbox.addTab(self.addon_widget, 'Addon Manager')

        # # Import
        self.import_widget = DataImportWidget(self)
        self.import_widget.add_data_btn.clicked.connect(self.extend_channelset)
        self.import_widget.rep_data_btn.clicked.connect(self.replace_channelset)
        self.global_toolbox.addTab(self.import_widget, 'Import Files')

        # # Export
        self.export_widget = DataExportWidget(self)
        self.global_toolbox.addTab(self.export_widget, 'Export Files')

        self.global_master_toolbox.add_toolbox(self.global_toolbox)

    def _update_splitter(self):
        # Get the current sizes of everything
        sizes = self.splitter.sizes()
        # Adjust the size of the sender to be equal to its size hint
        for i in range(self.splitter.count()):
            if self.sender() == self.splitter.widget(i):
                sizes[i] = self.sender().sizeHint().width()
        # Set the sizes
        self.splitter.setSizes(sizes)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)

    #---------------------- Acquisition window methods ------------------------
    def open_acquisition_window(self):
        if not self.acquisition_window:
            recType, configs = self.device_config.read_device_config()
            if not any([c is None for c in configs]):
                self.acquisition_window = AcquisitionWindow(self, recType, configs)
            else:
                self.acquisition_window = AcquisitionWindow(self)
            self.acquisition_window.done.connect(self.close_acquisition_window)
            self.acquisition_window.dataSaved.connect(self.receive_data)
            self.acquisition_window.show()

    def receive_data(self, tab_number=0):
        self.update_channelset()
        self.goto_time_series(switch_to_tab=False)
        self.goto_frequency_spectrum(switch_to_tab=False)
        self.goto_sonogram(switch_to_tab=False)
        self.goto_circle_fit(switch_to_tab=False)

        if self.sender() == self.acquisition_window:
            self.display_tabwidget.setCurrentIndex(tab_number)
            if tab_number == 1:
                self.set_freq_plot_type('Transfer Function')

    def close_acquisition_window(self):
        self.acquisition_window.done.disconnect()
        self.acquisition_window = None

    #---------------------------- Tab methods ---------------------------------
    def goto_time_series(self, switch_to_tab=True):
        if switch_to_tab:
            self.display_tabwidget.setCurrentWidget(self.timedomain_widget)
        self.timedomain_widget.set_selected_channels(self.channel_select_widget.selected_channels())

    def goto_frequency_spectrum(self, switch_to_tab=True):
        if switch_to_tab:
            # Switch to frequency domain tab
            self.display_tabwidget.setCurrentWidget(self.freqdomain_widget)
        self.freqdomain_widget.set_selected_channels(self.channel_select_widget.selected_channels())
        self.freqdomain_widget.calculate_spectrum()
        self.frequency_toolbox.set_plot_spectrum()

    def goto_transfer_function(self, switch_to_tab=True):
        if switch_to_tab:
            self.display_tabwidget.setCurrentWidget(self.freqdomain_widget)
        self.freqdomain_widget.set_selected_channels(self.channel_select_widget.selected_channels())
        # TODO: calculate TF function if none is found
        self.freqdomain_widget.calculate_transfer_function()
        self.frequency_toolbox.set_plot_transfer_function()

    def goto_sonogram(self, switch_to_tab=True):
        if switch_to_tab:
            self.display_tabwidget.setCurrentWidget(self.sonogram_widget)
        self.sonogram_widget.set_selected_channels(self.channel_select_widget.selected_channels())

    def goto_circle_fit(self, switch_to_tab=True):
        if switch_to_tab:
            self.display_tabwidget.setCurrentWidget(self.circle_widget)
        self.circle_widget.set_selected_channels(self.channel_select_widget.selected_channels())

    #------------------ ChannelSet methods ------------------------------------
    def create_test_channelset(self):
        self.cs = ChannelSet(5)
        t = np.arange(0,0.5,1/5000)
        for i, channel in enumerate(self.cs.channels):
            self.cs.set_channel_metadata(i,{'sample_rate': 5000})
            self.cs.add_channel_dataset(i, 'time_series', np.sin(t*2*np.pi*100*(i+1)))
            channel.name = "Channel {}".format(i)
        self.cs.add_channel_dataset(i,'time_series', np.sin(t*2*np.pi*100*(i+1))*np.exp(-t/t[-1]))

    def extend_channelset(self, cs):
        self.cs.channels.extend(cs.channels)
        self.update_channelset()

    def replace_channelset(self, cs):
        self.cs = cs
        self.update_channelset()

    def set_selected_channels(self, channels):
        # Set all the widget channels
        for i in range(self.display_tabwidget.count()):
            self.display_tabwidget.widget(i).set_selected_channels(channels)
        self.sonogram_toolbox.set_selected_channels(channels)

    def update_channelset(self):
        self.channel_select_widget.set_channel_set(self.cs)
        self.channel_metadata_widget.set_channel_set(self.cs)
        self.export_widget.set_channel_set(self.cs)


if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()
    w.show()

    sys.exit(app.exec_())

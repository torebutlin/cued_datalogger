import sys,traceback

if __name__ == '__main__':
    sys.path.append('../')

from PyQt5.QtCore import QCoreApplication, QSize, Qt,QTimer, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QApplication, QTabWidget, QGridLayout, QHBoxLayout,
                             QMainWindow, QPushButton, QMouseEventTransition,
                             QTabBar, QSplitter,QStackedLayout,QLabel, QSizePolicy, QStackedWidget,
                             QVBoxLayout,QFormLayout,QGroupBox,QRadioButton,QButtonGroup,QComboBox,
                             QLineEdit,QAction,QMenu, QCheckBox,QFileDialog)
from PyQt5.QtGui import QPalette,QColor

from datalogger.analysis.circle_fit import CircleFitWidget
from datalogger.analysis.sonogram import SonogramWidget
from datalogger.analysis.time_domain import TimeDomainWidget
from datalogger.analysis.frequency_domain import FrequencyDomainWidget

import pyqtgraph as pg
import numpy as np
from numpy.fft import rfft, rfftfreq

from datalogger.api.channel import ChannelSet, ChannelSelectWidget, ChannelMetadataWidget
from datalogger.api.addons import AddonManager
from datalogger.api.DataAnalysisPlot import DataPlotWidget
from datalogger.api.file_import import import_from_mat, DataImportWidget
from datalogger.liveplotUI import DevConfigUI,ChanToggleUI
import datalogger.liveplotUI  as lpUI

COLLAPSE_FACTOR = 0.7

class CollapsingSideTabWidget(QSplitter):
    def __init__(self, widget_side='left',parent = None):
        super().__init__(parent)

        self.parent = parent
        self.collapsetimer = QTimer(self)
        self.collapsetimer.timeout.connect(self.update_splitter)

        #self.prev_sz = None

        self.spacer = QWidget(self)
        self.spacer.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Ignored)

        # # Create the tab bar
        self.tabBar = QTabBar(self)

        self.tabBar.setTabsClosable(False)
        self.tabBar.setMovable(False)

        # # Create the Stacked widget
        self.tabPages = QStackedWidget(self)
        
        # # Link the signals
        #self.tabBar.tabBarDoubleClicked.connect(self.toggle_collapse)
        self.tabBar.currentChanged.connect(self.changePage)

        # # Add them to self
        if widget_side == 'left':
            self.tabBar.setShape(QTabBar.RoundedEast)
            self.addWidget(self.tabPages)
            self.addWidget(self.tabBar)
            self.addWidget(self.spacer)
            self.PAGE_IND = 0
            self.SPACE_IND = 2
        if widget_side == 'right':
            self.addWidget(self.spacer)
            self.tabBar.setShape(QTabBar.RoundedWest)
            self.addWidget(self.tabBar)
            self.addWidget(self.tabPages)
            self.PAGE_IND = 2
            self.SPACE_IND = 0

        self.setHandleWidth(2)
        self.setChildrenCollapsible(False)
        #for hd in [self.handle(i) for i in range(self.count())]:
        #    hd.setDisabled(True)
        self.spacer.hide()
        
    def addTab(self, widget, title):
        self.tabBar.addTab(title)
        self.tabPages.addWidget(widget)

    def toggle_collapse(self):
        self.spacer.show()
        self.parent.collapsed = not self.parent.collapsed
        sz = self.sizes()
        self.tabPages.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Ignored)
        sz[1] = self.tabBar.sizeHint().width()
        if self.parent.collapsed:
            sz[self.SPACE_IND] = 10
            sz[self.PAGE_IND] = 200
        else:
            self.tabPages.show()
            sz[self.PAGE_IND] = 10
            sz[self.SPACE_IND] = 200
        self.setSizes(sz)
        self.collapsetimer.start(25)

    def changePage(self, index):
        self.tabBar.setCurrentIndex(index)
        self.tabPages.setCurrentIndex(index)

    def clear(self):
        for i in range(self.tabBar.count()):
            self.tabBar.removeTab(0)
            self.tabPages.removeWidget(self.tabPages.currentWidget())

    def update_splitter(self):
        sz = self.sizes()
        sz[1] = self.tabBar.sizeHint().width()
        if self.parent.collapsed:
            if not sz[self.PAGE_IND] < 5:
                sz[self.SPACE_IND] += sz[self.PAGE_IND] * COLLAPSE_FACTOR
                sz[self.PAGE_IND] *= COLLAPSE_FACTOR
            else:
                self.tabPages.hide()
                self.spacer.hide()
                self.collapsetimer.stop()
        else:
            if not sz[self.SPACE_IND] <5:
                sz[self.SPACE_IND] -= sz[self.PAGE_IND] * COLLAPSE_FACTOR
                sz[self.PAGE_IND] *= 1+COLLAPSE_FACTOR
            else:
                self.tabPages.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred)
                self.spacer.hide()
                self.collapsetimer.stop()
        self.setSizes(sz)

class StackedToolbox(QStackedWidget):
    """A stack of CollapsingSideTabWidgets"""
    def __init__(self):
        super().__init__()
        
        self.collapsed = False
                #self.widget(i).toggle_collapse()
        #self.layout().setStackingMode(QStackedLayout.StackAll)

    def toggleCollapse(self):
        """Toggle collapse of all the widgets in the stack"""
        self.currentWidget().toggle_collapse()
        
    def show_toolbox(self,num):
        for i in range(self.count()):
            if not i == num:
                self.widget(i).tabPages.hide()
            
    def switch_toolbox(self,num):
        self.currentWidget().tabPages.hide()
        if not self.collapsed:
            self.widget(num).tabPages.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred)
            self.widget(num).tabPages.show()
        self.setCurrentIndex(num)
            
    def addToolbox(self, toolbox):
        """Add a toolbox to the stack"""
        toolbox.parent = self
        toolbox.setParent(self)
        toolbox.tabBar.tabBarDoubleClicked.connect(self.toggleCollapse)
        self.addWidget(toolbox)

class AnalysisDisplayTabWidget(QTabWidget):
    def __init__(self, *arg, **kwarg):
        super().__init__(*arg, **kwarg)

        self.init_ui()

    def init_ui(self):
        self.setMovable(False)
        self.setTabsClosable(False)

        self.timedomain_widget = DataPlotWidget(self)
        self.freqdomain_widget = DataPlotWidget(self)
        self.sonogram_widget = SonogramWidget(self)
        self.circle_widget = CircleFitWidget(self)
                
        # Create the tabs
        self.addTab(self.timedomain_widget, "Time Domain")
        self.addTab(self.freqdomain_widget, "Frequency Domain")
        self.addTab(self.sonogram_widget, "Sonogram")
        self.addTab(self.circle_widget, "Modal Fitting")

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
        self.toolbox = StackedToolbox()
        
        self.time_toolbox = CollapsingSideTabWidget('left',self.toolbox)
        wd = QWidget(self)
        hb = QVBoxLayout(wd)
        fft_btn = QPushButton("Convert to FFT",self.time_toolbox)
        fft_btn.clicked.connect(self.plot_fft)
        sono_btn = QPushButton("Sonogram",self.time_toolbox)
        sono_btn.clicked.connect(self.plot_sonogram)
        hb.addWidget(fft_btn)
        hb.addWidget(sono_btn)
        self.time_toolbox.addTab(wd, "TimeTab1")
        self.time_toolbox.addTab(QPushButton("Button 2",self.time_toolbox), "TimeTab2")

        self.frequency_toolbox = CollapsingSideTabWidget('left',self.toolbox)
        wd2 = QWidget(self)
        hb2 = QVBoxLayout(wd2)
        circle_btn = QPushButton("Circle_Fit",self.frequency_toolbox)
        hb2.addWidget(circle_btn)
        circle_btn.clicked.connect(self.circle_fitting)
        self.frequency_toolbox.addTab(wd2, "Conversion")
        self.frequency_toolbox.addTab(QPushButton("Button 2",self.frequency_toolbox), "FreqTab2")

        self.sonogram_toolbox = CollapsingSideTabWidget('left',self.toolbox)
        self.sonogram_toolbox.addTab(QPushButton("Button 1",self.sonogram_toolbox), "SonTab1")
        self.sonogram_toolbox.addTab(QPushButton("Button 2",self.sonogram_toolbox), "SonTab2")

        self.modal_analysis_toolbox = CollapsingSideTabWidget('left',self.toolbox)
        self.modal_analysis_toolbox.addTab(QPushButton("Button 1",self.modal_analysis_toolbox), "ModalTab1")
        self.modal_analysis_toolbox.addTab(QPushButton("Button 2",self.modal_analysis_toolbox), "ModalTab2")       
        
        self.toolbox.addToolbox(self.time_toolbox)
        self.toolbox.addToolbox(self.frequency_toolbox)
        self.toolbox.addToolbox(self.sonogram_toolbox)
        self.toolbox.addToolbox(self.modal_analysis_toolbox)
        self.toolbox.show_toolbox(0)

    def init_global_toolbox(self):        
        self.global_toolbox = StackedToolbox()
        self.gtools = CollapsingSideTabWidget('right',self.global_toolbox)
        
        self.liveplot = None
        dev_configUI = DevConfigUI()
        dev_configUI.config_button.setText('Open Oscilloscope')
        dev_configUI.config_button.clicked.connect(self.open_liveplot)
        self.gtools.addTab(dev_configUI,'Oscilloscope')

        self.channel_select_widget = ChannelSelectWidget(self.gtools)
        self.channel_select_widget.channel_selection_changed.connect(self.display_channel_plots)
        self.gtools.addTab(self.channel_select_widget, 'Channel Selection')

        self.channel_metadata_widget = ChannelMetadataWidget(self.gtools)
        self.gtools.addTab(self.channel_metadata_widget, 'Channel Metadata')

        
        self.channel_metadata_widget.metadataChange.connect(self.update_cs)
            
        self.addon_widget = AddonManager(self)
        self.gtools.addTab(self.addon_widget, 'Addon Manager')

        self.import_widget = DataImportWidget(self)
        self.import_widget.add_data_btn.clicked.connect(lambda: self.add_import_data('Extend'))
        self.import_widget.rep_data_btn.clicked.connect(lambda: self.add_import_data('Replace'))
        self.gtools.addTab(self.import_widget, 'Import Files')
        
        self.global_toolbox.addToolbox(self.gtools)
        
    def update_cs(self,cs):
        self.channel_select_widget.cs = self.cs = cs
        self.channel_select_widget.set_channel_name()
            
    def init_ui(self):
        menubar = self.menuBar()
        menubar.addMenu(ProjectMenu(self))

        # # Create the main widget
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)

       # Create the toolbox
        self.init_toolbox()

        # Create the global toolbox
        self.init_global_toolbox()

        # Create the analysis tools tab widget
        self.display_tabwidget = AnalysisDisplayTabWidget(self)
        self.display_tabwidget.currentChanged.connect(self.toolbox.switch_toolbox)
        
        self.plot_colours = ['r','g','b', 'k', 'm']
        self.timeplots = []
        self.freqplots = []
        
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
            
    def open_liveplot(self):
        if not self.liveplot:
            self.liveplot = lpUI.LiveplotApp(self)
            self.liveplot.done.connect(self.done_liveplot)
            self.liveplot.dataSaved.connect(self.plot_time_series)
            self.liveplot.dataSaved.connect(self.config_channelset)
            self.liveplot.show()

    def done_liveplot(self):
        self.liveplot.done.disconnect()
        self.liveplot = None
     
    def config_channelset(self):
        self.channel_select_widget.set_channel_set(self.cs)
        self.channel_metadata_widget.set_channel_set(self.cs)
    
    def plot_time_series(self):
        self.display_tabwidget.freqdomain_widget.resetPlotWidget()
        self.display_tabwidget.setCurrentWidget(self.display_tabwidget.timedomain_widget)

        data = self.cs.get_channel_data(tuple(range(len(self.cs))),'time_series')
        # Note: channel without a time series will give an empty array
        self.timeplots = []
        self.display_tabwidget.currentWidget().resetPlotWidget()
        data_end = 0
        for i,dt in enumerate(data):
            if not dt.shape[0] == 0:
                sample_rate = self.cs.get_channel_metadata(i,'sample_rate')
                t = np.arange(dt.shape[0])/sample_rate
                self.timeplots.append(self.display_tabwidget.timedomain_widget.\
                                      plotitem.plot(t,dt,pen = self.plot_colours[i%len(self.plot_colours)]))
                data_end = max(data_end,t[-1])
            else:
                # Empty array will plot nothing and thus None in timeplots
                self.timeplots.append(None)
        
        # Set up the spinboxes and plot ranges
        self.display_tabwidget.timedomain_widget.sp1.setSingleStep(data_end/100) 
        self.display_tabwidget.timedomain_widget.sp2.setSingleStep(data_end/100) 
        self.display_tabwidget.timedomain_widget.sp1.setValue(data_end*0.4)
        self.display_tabwidget.timedomain_widget.sp2.setValue(data_end*0.6)
        self.display_tabwidget.timedomain_widget.plotitem.setLimits(xMin = 0,
                                                                    xMax = data_end)
        self.display_tabwidget.timedomain_widget.plotitem.setRange(xRange = (0,data_end),
                                                                   padding = 0.2)
        
    def plot_fft(self):
        # Switch to frequency domain tab
        self.display_tabwidget.setCurrentWidget(self.display_tabwidget.freqdomain_widget)
        self.display_tabwidget.currentWidget().resetPlotWidget()
        self.freqplots = []
        
        tdata = self.cs.get_channel_data(tuple(range(len(self.cs))),'time_series')
        fdata = self.cs.get_channel_data(tuple(range(len(self.cs))),'spectrum')
        
        data_end = 0
        max_data = 0
        for i in range(len(self.cs)):
            if not fdata[i].shape[0] == 0 or not tdata[i].shape[0] == 0:
                sample_rate = self.cs.get_channel_metadata(i,'sample_rate')
                if not fdata[i].shape[0] == 0:
                    f = np.arange(int(fdata[i].shape[0]))/fdata[i].shape[0] * sample_rate
                    ft = np.abs(fdata[i])
                elif not tdata[i].shape[0] == 0:
                    print('Calculating Spectrum from timeseries')
                    f = np.arange(int(tdata[i].shape[0]/2)+1)/tdata[i].shape[0] * sample_rate
                    ft = np.abs(np.real(rfft(tdata[i])))
                    self.cs.add_channel_dataset(i,'spectrum', ft)
                self.freqplots.append(self.display_tabwidget.freqdomain_widget.plotitem.plot(f,ft,pen = self.plot_colours[i%len(self.plot_colours)]))
                data_end = max(data_end,f[-1])
                max_data = max(max_data,max(ft))
            else:
                print('No specturm to plot')
                self.freqplots.append(None)
                return
          
        self.display_tabwidget.freqdomain_widget.sp1.setSingleStep(data_end/100)
        self.display_tabwidget.freqdomain_widget.sp2.setSingleStep(data_end/100)
        
        self.display_tabwidget.freqdomain_widget.sp1.setValue(data_end*0.4)
        self.display_tabwidget.freqdomain_widget.sp2.setValue(data_end*0.6)
        self.display_tabwidget.freqdomain_widget.plotitem.setLimits(xMin = 0,
                                                                    xMax = data_end)
        self.display_tabwidget.freqdomain_widget.plotitem.setRange(xRange = (0,data_end),
                                                                   yRange = (0,max_data),
                                                                   padding = 0.2)
     
    def plot_sonogram(self):
        signal = self.cs.get_channel_data(0,'time_series')
        if not signal.shape[0] == 0:
            self.display_tabwidget.setCurrentWidget(self.display_tabwidget.sonogram_widget)
            self.display_tabwidget.currentWidget().plot(signal)
        
    def circle_fitting(self):
        self.display_tabwidget.setCurrentWidget(self.display_tabwidget.circle_widget)
        fdata = self.cs.get_channel_data(0, "spectrum")
        self.display_tabwidget.circle_widget.transfer_function_type = 'acceleration'
        self.display_tabwidget.circle_widget.set_data(np.linspace(0, self.cs.get_channel_metadata(0, "sample_rate"), fdata.size), fdata)
        
    def display_channel_plots(self, selected_channel_list):
        self.display_tabwidget.timedomain_widget.resetPlotWidget()
        self.display_tabwidget.freqdomain_widget.resetPlotWidget()
        timeplotitem = self.display_tabwidget.timedomain_widget.plotitem
        freqplotitem = self.display_tabwidget.freqdomain_widget.plotitem
        for i, channel in enumerate(self.cs.channels):
            if i in selected_channel_list:
                if i< len(self.timeplots):
                    if self.timeplots[i]:
                        timeplotitem.addItem(self.timeplots[i])
                else:
                    self.timeplots.append(None)
                    
                if i< len(self.freqplots): 
                    if self.freqplots[i]:
                        freqplotitem.addItem(self.freqplots[i])
                else:
                    self.freqplots.append(None)
                
    def add_import_data(self,mode):
        if mode == 'Extend':
            self.cs.channels.extend(self.import_widget.new_cs.channels) 
        elif mode == 'Replace':
            self.cs = self.import_widget.new_cs
        
        self.config_channelset()
        self.plot_time_series()
        self.plot_fft()
        self.display_tabwidget.setCurrentWidget(self.display_tabwidget.timedomain_widget)
        
        self.import_widget.clear()
        
    
if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()
    w.show()

    sys.exit(app.exec_())

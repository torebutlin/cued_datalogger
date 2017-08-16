import sys,traceback

if __name__ == '__main__':
    sys.path.append('../')

from PyQt5.QtCore import QCoreApplication, QSize, Qt,QTimer, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QApplication, QTabWidget, QGridLayout, QHBoxLayout,
                             QMainWindow, QPushButton, QMouseEventTransition,
                             QTabBar, QSplitter,QStackedLayout,QLabel, QSizePolicy, QStackedWidget,
                             QVBoxLayout,QFormLayout,QGroupBox,QRadioButton,QButtonGroup,QComboBox,
                             QLineEdit,QAction,QMenu, QCheckBox)
from PyQt5.QtGui import QPalette,QColor

from analysis.circle_fit import CircleFitWidget
from analysis.sonogram import SonogramWidget
from analysis.time_domain import TimeDomainWidget
from analysis.frequency_domain import FrequencyDomainWidget

import pyqtgraph as pg
import numpy as np
from numpy.fft import rfft, rfftfreq

from bin.channel import ChannelSet, ChannelSelectWidget, ChannelMetadataWidget
from bin.addons import AddonManager
from bin.DataAnalysisPlot import DataPlotWidget
from liveplotUI import DevConfigUI,ChanToggleUI
import liveplotUI  as lpUI

COLLAPSE_FACTOR = 0.7

class CollapsingSideTabWidget(QSplitter):
    def __init__(self, widget_side='left',parent = None):
        super().__init__(parent)

        self.parent = parent
        self.collapsetimer = QTimer(self)
        self.collapsetimer.timeout.connect(self.update_splitter)

        self.collapsed = False
        self.prev_sz = None

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
        self.collapsed = not self.collapsed
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
        self.tabPages.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Ignored)
        sz[1] = self.tabBar.sizeHint().width()
        if self.collapsed:
            if not sz[self.PAGE_IND] < 5:
                sz[self.SPACE_IND] += sz[self.PAGE_IND] * COLLAPSE_FACTOR
                sz[self.PAGE_IND] *= COLLAPSE_FACTOR
            else:
                self.prev_sz = sz
                self.tabPages.hide()
                
                print(self.prev_sz)
                self.spacer.hide()
                self.collapsetimer.stop()
        else:
            self.tabPages.show()
            sz = self.prev_sz
            if not sz[self.SPACE_IND] <5:
                sz[self.SPACE_IND] -= sz[self.PAGE_IND] * COLLAPSE_FACTOR
                sz[self.PAGE_IND] *= 1+COLLAPSE_FACTOR
            else:
                self.tabPages.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred)
                self.spacer.hide()
                print(self.prev_sz)
                self.collapsetimer.stop()
        self.setSizes(sz)

class StackedToolbox(QStackedWidget):
    """A stack of CollapsingSideTabWidgets"""
    def __init__(self):
        super().__init__()
        #self.layout().setStackingMode(QStackedLayout.StackAll)

    def toggleCollapse(self):
        """Toggle collapse of all the widgets in the stack"""
        for i in range(self.count()):
            self.widget(i).toggle_collapse()

    def addToolbox(self, toolbox):
        """Add a toolbox to the stack"""
        # Make sure that when this toolbox is collapsed, all the toolboxes
        # collapse
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
        # Create the tabs
        self.addTab(self.timedomain_widget, "Time Domain")
        self.addTab(self.freqdomain_widget, "Frequency Domain")
        self.addTab(self.sonogram_widget, "Sonogram")
        self.addTab(CircleFitWidget(self), "Modal Fitting")

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
    def __init__(self):
        super().__init__()

        self.setGeometry(500,300,800,500)
        self.setWindowTitle('AnalysisWindow')

        #self.prepare_tools()
        self.create_test_channelset()
        self.init_ui()

        self.setFocus()
        self.show()

    def init_toolbox(self):
        self.time_toolbox = CollapsingSideTabWidget('left',self)
        wd = QWidget(self)
        hb = QHBoxLayout(wd)
        fft_btn = QPushButton("Convert to FFT",self.time_toolbox)
        fft_btn.clicked.connect(self.plot_fft)
        sono_btn = QPushButton("Sonogram",self.time_toolbox)
        sono_btn.clicked.connect(self.plot_sonogram)
        hb.addWidget(fft_btn)
        hb.addWidget(sono_btn)
        self.time_toolbox.addTab(wd, "TimeTab1")
        self.time_toolbox.addTab(QPushButton("Button 2",self.time_toolbox), "TimeTab2")

        self.frequency_toolbox = CollapsingSideTabWidget('left',self)
        self.frequency_toolbox.addTab(QPushButton("Button 1",self.frequency_toolbox), "FreqTab1")
        self.frequency_toolbox.addTab(QPushButton("Button 2",self.frequency_toolbox), "FreqTab2")

        self.sonogram_toolbox = CollapsingSideTabWidget('left',self)
        self.sonogram_toolbox.addTab(QPushButton("Button 1",self.sonogram_toolbox), "SonTab1")
        self.sonogram_toolbox.addTab(QPushButton("Button 2",self.sonogram_toolbox), "SonTab2")

        self.modal_analysis_toolbox = CollapsingSideTabWidget('left',self)
        self.modal_analysis_toolbox.addTab(QPushButton("Button 1",self.modal_analysis_toolbox), "ModalTab1")
        self.modal_analysis_toolbox.addTab(QPushButton("Button 2",self.modal_analysis_toolbox), "ModalTab2")

        self.toolbox = StackedToolbox()
        self.toolbox.addToolbox(self.time_toolbox)
        self.toolbox.addToolbox(self.frequency_toolbox)
        self.toolbox.addToolbox(self.sonogram_toolbox)
        self.toolbox.addToolbox(self.modal_analysis_toolbox)

    def init_global_toolbox(self):
        self.gtools = CollapsingSideTabWidget('right',self)
        
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

        self.addon_widget = AddonManager(self)
        self.gtools.addTab(self.addon_widget, 'Addon Manager')

        self.global_toolbox = StackedToolbox()
        self.global_toolbox.addToolbox(self.gtools)

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
        self.display_tabwidget.currentChanged.connect(self.toolbox.setCurrentIndex)
        self.display_tabwidget.currentChanged.connect(self.update)
        
        self.plot_colours = ['r','g','b', 'k', 'm']
        self.timeplots = []
        self.freqplots = []
        
        self.config_channelset()
        self.plot_time_series()

        #self.chantoggle_ui.chan_btn_group.buttonClicked.connect(self.display_channel_plots)

        # Add the widgets
        self.main_layout.addWidget(self.toolbox)
        self.main_layout.addWidget(self.display_tabwidget)
        self.main_layout.addWidget(self.global_toolbox)
        # Set the stretch factors
        self.main_layout.setStretchFactor(self.toolbox, 0)
        self.main_layout.setStretchFactor(self.display_tabwidget, 1)
        self.main_layout.setStretchFactor(self.global_toolbox, 0)
        
    def create_test_channelset(self):
        self.cs = ChannelSet(5)

        t = np.arange(1000)/44100
        for i, channel in enumerate(self.cs.channels):
            self.cs.add_channel_dataset(i, 'timeseries', np.sin(t*2*np.pi*100*(i+1)))
            self.cs.add_channel_dataset(i,'freqseries', []) 
            
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
        data = self.cs.get_channel_data(tuple(range(len(self.cs))),'timeseries')
        self.timeplots = []
        self.display_tabwidget.currentWidget().resetPlotWidget()
        for dt,p in zip(data, self.plot_colours):
            self.timeplots.append(self.display_tabwidget.timedomain_widget.plotitem.plot(dt,pen = p))
        
        self.display_tabwidget.timedomain_widget.sp1.setSingleStep(int(len(data[0])/100)) 
        self.display_tabwidget.timedomain_widget.sp2.setSingleStep(int(len(data[0])/100)) 
        
        self.display_tabwidget.timedomain_widget.sp1.setValue(int(len(data[0])*0.4))
        self.display_tabwidget.timedomain_widget.sp2.setValue(int(len(data[0])*0.6))
        self.display_tabwidget.timedomain_widget.plotitem.setLimits(xMin = 0,
                                                                    xMax = len(data[0]))
        self.display_tabwidget.timedomain_widget.plotitem.setRange(xRange = (0,len(data[0])),
                                                                   padding = 0.2)
        self.display_channel_plots(self.channel_select_widget.selected_channels())
        
    def plot_fft(self):
        # Switch to frequency domain tab
        self.display_tabwidget.setCurrentWidget(self.display_tabwidget.freqdomain_widget)
        data = self.cs.get_channel_data(tuple(range(len(self.cs))),'timeseries')

        self.freqplots = []
        self.display_tabwidget.currentWidget().resetPlotWidget()
        for dt,p,i in zip(data, self.plot_colours,range(len(self.cs))):
            # Calculate FT and associated frequencies
            ft = np.abs(np.real(rfft(dt)))
            #freqs = np.real(rfftfreq(dt.size, 1/4096))
            self.freqplots.append(self.display_tabwidget.freqdomain_widget.plotitem.plot(ft,pen = p))
            self.cs.set_channel_data(i,'freqseries', ft)     
            
        self.display_tabwidget.freqdomain_widget.sp1.setSingleStep(int(len(data[0])/100)) 
        self.display_tabwidget.freqdomain_widget.sp2.setSingleStep(int(len(data[0])/100)) 
        
        self.display_tabwidget.freqdomain_widget.sp1.setValue(int(len(data[0])*0.4))
        self.display_tabwidget.freqdomain_widget.sp2.setValue(int(len(data[0])*0.6))
        self.display_tabwidget.freqdomain_widget.plotitem.setLimits(xMin = 0,
                                                                    xMax = len(ft))
        self.display_tabwidget.freqdomain_widget.plotitem.setRange(xRange = (0,len(ft)),
                                                                   yRange = (0,np.max(ft)),
                                                                   padding = 0.2)
        self.display_channel_plots(self.channel_select_widget.selected_channels())
     
    def plot_sonogram(self):
        self.display_tabwidget.setCurrentWidget(self.display_tabwidget.sonogram_widget)
        signal = self.cs.get_channel_data(0,'timeseries')
        self.display_tabwidget.currentWidget().plot(signal)
        
    def display_channel_plots(self, selected_channel_list):
        #plotitem = self.display_tabwidget.timedomain_widget.plotitem
        self.display_tabwidget.timedomain_widget.resetPlotWidget()
        self.display_tabwidget.freqdomain_widget.resetPlotWidget()
        timeplotitem = self.display_tabwidget.timedomain_widget.plotitem
        freqplotitem = self.display_tabwidget.freqdomain_widget.plotitem
        #plotitem.clear()
        for i, channel in enumerate(self.cs.channels):
            if i in selected_channel_list:
                if self.timeplots:
                    timeplotitem.addItem(self.timeplots[i])
                if self.freqplots:
                    freqplotitem.addItem(self.freqplots[i])
                


if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()
    w.show()

    sys.exit(app.exec_())

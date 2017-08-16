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

from bin.channel import ChannelSet, ChannelSelectWidget, ChannelMetadataWidget
from bin.addons import AddonManager
from bin.DataAnalysisPlot import DataPlotWidget
from liveplotUI import DevConfigUI,ChanToggleUI
import liveplotUI  as lpUI

COLLAPSE_FACTOR = 0.7

class CollapsingSideTabWidget(QSplitter):
    def __init__(self, widget_side='left'):
        super().__init__()

        self.collapsetimer = QTimer(self)
        self.collapsetimer.timeout.connect(self.update_splitter)

        self.collapsed = False
        self.prev_sz = None

        self.spacer = QWidget(self)
        self.spacer.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Ignored)

        # # Create the tab bar
        self.tabBar = QTabBar()

        self.tabBar.setTabsClosable(False)
        self.tabBar.setMovable(False)

        # # Create the Stacked widget
        self.tabPages = QStackedWidget()

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
        self.TAB_SIZE = self.tabBar.sizeHint().width()

        self.setHandleWidth(1)
        for hd in [self.handle(i) for i in range(self.count())]:
            hd.setDisabled(True)
        self.spacer.hide()

    def addTab(self, widget, title):
        self.tabBar.addTab(title)
        self.tabPages.addWidget(widget)

    def toggle_collapse(self):
        self.spacer.show()
        self.collapsed = not self.collapsed
        self.collapsetimer.start(20)

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
                self.collapsetimer.stop()
        self.setSizes(sz)

class StackedToolbox(QStackedWidget):
    """A stack of CollapsingSideTabWidgets"""
    def __init__(self):
        super().__init__()
        self.layout().setStackingMode(QStackedLayout.StackAll)

    def toggleCollapse(self):
        """Toggle collapse of all the widgets in the stack"""
        for i in range(self.count()):
            # The current one will toggle by default, so we don't want
            # to toggle it again
            #if i == self.currentIndex():
            #    continue
            #else:
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
        # Create the tabs
        self.addTab(self.timedomain_widget, "Time Domain")
        self.addTab(FrequencyDomainWidget(self), "Frequency Domain")
        self.addTab(SonogramWidget(self), "Sonogram")
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
        self.time_toolbox = CollapsingSideTabWidget('left')
        self.time_toolbox.addTab(QPushButton("Button 1"), "TimeTab1")
        self.time_toolbox.addTab(QPushButton("Button 2"), "TimeTab2")

        self.frequency_toolbox = CollapsingSideTabWidget('left')
        self.frequency_toolbox.addTab(QPushButton("Button 1"), "FreqTab1")
        self.frequency_toolbox.addTab(QPushButton("Button 2"), "FreqTab2")

        self.sonogram_toolbox = CollapsingSideTabWidget('left')
        self.sonogram_toolbox.addTab(QPushButton("Button 1"), "SonTab1")
        self.sonogram_toolbox.addTab(QPushButton("Button 2"), "SonTab2")

        self.modal_analysis_toolbox = CollapsingSideTabWidget('left')
        self.modal_analysis_toolbox.addTab(QPushButton("Button 1"), "ModalTab1")
        self.modal_analysis_toolbox.addTab(QPushButton("Button 2"), "ModalTab2")

        self.toolbox = StackedToolbox()
        self.toolbox.addToolbox(self.time_toolbox)
        self.toolbox.addToolbox(self.frequency_toolbox)
        self.toolbox.addToolbox(self.sonogram_toolbox)
        self.toolbox.addToolbox(self.modal_analysis_toolbox)

    def init_global_toolbox(self):
        self.gtools = CollapsingSideTabWidget('right')
        
        self.liveplot = None
        dev_configUI = DevConfigUI()
        dev_configUI.config_button.setText('Open Oscilloscope')
        dev_configUI.config_button.clicked.connect(self.open_liveplot)
        self.gtools.addTab(dev_configUI,'Oscilloscope')

        self.channel_select_widget = ChannelSelectWidget(self.gtools)
        #self.channel_select_widget.set_channel_set(self.cs)
        self.channel_select_widget.channel_selection_changed.connect(self.display_channel_plots)
        self.gtools.addTab(self.channel_select_widget, 'Channel Selection')

        self.channel_metadata_widget = ChannelMetadataWidget(self.gtools)
        #self.channel_metadata_widget.set_channel_set(self.cs)
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
        
        self.plot_colours = ['r','g','b', 'k', 'm']
        self.timeplots = []
        self.plot_time_series()
        self.config_channelset()

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
        data = self.cs.get_channel_data(tuple(range(len(self.cs))),'timeseries')
        self.timeplots = []
        for dt,p,i in zip(data, self.plot_colours, range(len(self.cs))):
            self.timeplots.append(self.display_tabwidget.timedomain_widget.plotitem.plot(dt,pen = p))
        
        self.display_tabwidget.timedomain_widget.sp1.setSingleStep(int(len(data[0])/100)) 
        self.display_tabwidget.timedomain_widget.sp2.setSingleStep(int(len(data[0])/100)) 
        
        print('a')
        self.display_tabwidget.timedomain_widget.sp1.setValue(int(len(data[0])*0.4))
        print('b')
        self.display_tabwidget.timedomain_widget.sp2.setValue(int(len(data[0])*0.2))
        print('c')
        print(self.display_tabwidget.timedomain_widget.sp1.value(),
              self.display_tabwidget.timedomain_widget.sp2.value())
        #self.display_tabwidget.timedomain_widget.updateRegion()
        self.display_tabwidget.timedomain_widget.plotitem.setLimits(xMin = 0,
                                                                    xMax = len(data[0]))
        self.display_tabwidget.timedomain_widget.plotitem.setRange(xRange = (0,len(data[0])),
                                                                   padding = 0.2)
        
    def display_channel_plots(self, selected_channel_list):
        #plotitem = self.display_tabwidget.timedomain_widget.plotitem
        self.display_tabwidget.timedomain_widget.resetPlotWidget()
        plotitem = self.display_tabwidget.timedomain_widget.plotitem
        #plotitem.clear()
        for i, channel in enumerate(self.cs.channels):
            if i in selected_channel_list:
                plotitem.addItem(self.timeplots[i])
                


if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()
    w.show()

    sys.exit(app.exec_())

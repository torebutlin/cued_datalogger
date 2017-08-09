import sys,traceback

if __name__ == '__main__':
    sys.path.append('../')

from PyQt5.QtCore import QCoreApplication, QSize, Qt
from PyQt5.QtWidgets import (QWidget, QApplication, QTabWidget, QGridLayout, QHBoxLayout,
                             QMainWindow, QPushButton, QMouseEventTransition, 
                             QTabBar, QSplitter,QStackedLayout,QLabel )
from PyQt5.QtGui import QSizePolicy

from circle_fit import CircleFitWidget
from sonogram import SonogramWidget
from time_domain import TimeDomainWidget
from frequency_domain import FrequencyDomainWidget

import pyqtgraph as pg

from bin.channel import ChannelSet


class SideTabWidget(QTabWidget):
    def __init__(self, widget_side='left'):
        super().__init__()

        #self.tabBar().tabBarDoubleClicked.connect(self.toggle_collapse)

        self.setMinimumWidth(1)
        self.setMaximumWidth(100)

        self.setTabsClosable(False)
        self.setMovable(False)

        if widget_side == 'left':
            self.setTabPosition(QTabWidget.East)
        if widget_side == 'right':
            self.setTabPosition(QTabWidget.West)

class collapsibleSideTabs(QWidget):
    def __init__(self, *arg, widget_side='left', **kwarg):
        super().__init__(*arg, **kwarg)
        
        self.UI_layout = QHBoxLayout(self)
        
        self.splitter = QSplitter(Qt.Horizontal,self)
        
        self.stack_widgets = QWidget(self.splitter)
        self.stack_layout = QStackedLayout(self.stack_widgets)
        self.stack_layout.addWidget(QLabel('Here',self.stack_widgets))
        self.stack_layout.addWidget(QLabel('There',self.stack_widgets))
        self.stack_layout.setCurrentIndex(0)
        
        
        self.tab_bar = QTabBar(self.splitter)
        self.tab_bar.addTab('Tab1')
        self.tab_bar.addTab('Tab2')
        self.tab_bar.setShape(QTabBar.RoundedEast)
        self.tab_bar.setCurrentIndex(0)
        self.tab_bar.currentChanged.connect(self.change_widget)
        
        self.analysistools_tabwidget = AnalysisTools_TabWidget(self)
        
        self.splitter.addWidget(self.stack_widgets)
        self.splitter.addWidget(self.tab_bar)
        self.splitter.addWidget(self.analysistools_tabwidget)
        
        self.tab_bar.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
        self.splitter.setStretchFactor(0,0)
        self.splitter.setStretchFactor(1,0)
        self.splitter.setStretchFactor(2,10)
        self.splitter.setCollapsible(1,False)
        
        self.UI_layout.addWidget(self.splitter)
        
        self.splitter.splitterMoved.connect(self.resize_self)
        
    def resize_self(self, pos,ind):
        w = min(pos-21,100)
        if ind == 1:
            self.splitter.setSizes([w,21,500-21-w])
        if ind == 2:
            self.splitter.setSizes([w,21,pos])
    
    def change_widget(self):

        self.stack_layout.setCurrentIndex(num)
        
class AnalysisTools_TabWidget(QTabWidget):
    def __init__(self, *arg, **kwarg):
        super().__init__(*arg, **kwarg)

        self.init_ui()

    def init_ui(self):
        self.setMovable(False)
        self.setTabsClosable(False)

        # Create the tabs
        self.addTab(TimeDomainWidget(self), "Time Domain")
        self.addTab(FrequencyDomainWidget(self), "Frequency Domain")
        self.addTab(SonogramWidget(self), "Sonogram")
        self.addTab(CircleFitWidget(self), "Modal Fitting")


class AnalysisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setGeometry(500,300,500,500)
        self.setWindowTitle('data')
        
        try:
            self.init_ui()
        except:
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))
            self.show()
            return

        self.setFocus()
        self.show()

        self.cs = ChannelSet()

    def init_ui(self):
        '''
        # # Create a statusbar, menubar, and toolbar
        self.statusbar = self.statusBar(self)
        self.menubar = self.menuBar(self)
        self.toolbar = self.addToolBar("Tools")

        # # Set up the menu bar
        self.menubar.addMenu("Project")
        self.menubar.addMenu("Data")
        self.menubar.addMenu("View")
        self.menubar.addMenu("Addons")
        '''
        # # Create the main widget
        self.main_widget = QWidget(self)
        self.main_layout = QHBoxLayout(self.main_widget)
        #self.main_widget.setLayout(self.main_layout)
        #self.main_widget = QWidget(self)
        # Add the sidetabwidget
        try:
            self.sidetabwidget = collapsibleSideTabs(self)
            self.main_layout.addWidget(self.sidetabwidget)
        except:
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))   
        

        # Add the analysis tools tab widget
        #self.analysistools_tabwidget = AnalysisTools_TabWidget(self)
        #self.main_widget.addWidget(self.analysistools_tabwidget)
        
        #self.main_widget.setChildrenCollapsible(False)
        self.setCentralWidget(self.main_widget)


if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()

    sys.exit(app.exec_())

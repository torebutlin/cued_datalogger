import sys,traceback

if __name__ == '__main__':
    sys.path.append('../')

from PyQt5.QtCore import QCoreApplication, QSize, Qt
from PyQt5.QtWidgets import (QWidget, QApplication, QTabWidget, QGridLayout, QHBoxLayout,
                             QMainWindow, QPushButton, QMouseEventTransition,
                             QTabBar, QSplitter,QStackedLayout,QLabel, QSizePolicy)
from PyQt5.QtGui import QPalette,QColor

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

        self.collapsed = False

        self.UI_layout = QHBoxLayout(self)

        self.splitter = QSplitter(Qt.Horizontal,self)

        self.stack_widgets = QWidget(self.splitter)
        self.stack_layout = QStackedLayout(self.stack_widgets)
        lb1 = QLabel('Here',self.stack_widgets)
        lb1.setAutoFillBackground(False)
        self.stack_layout.addWidget(lb1)
        self.stack_layout.addWidget(QLabel('There',self.stack_widgets))
        self.stack_layout.setCurrentIndex(0)
        '''
        pal = QPalette()
        pal.setColor(QPalette.Background, QColor(255,255,255))
        pal.setColor(QPalette.Base, QColor(255,255,255))
        self.stack_widgets.setAutoFillBackground(True)
        self.stack_widgets.setPalette(pal)
        '''
        
        self.tab_bar = QTabBar(self.splitter)
        self.tab_bar.addTab('Tab1')
        self.tab_bar.addTab('Tab2')
        self.tab_bar.setShape(QTabBar.RoundedEast)
        self.tab_bar.setCurrentIndex(0)
        self.tab_bar.currentChanged.connect(self.change_widget)
        self.tab_bar.tabBarDoubleClicked.connect(self.toggle_collapse)

        self.splitter.addWidget(self.stack_widgets)
        self.splitter.addWidget(self.tab_bar)

        self.tab_bar.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
        self.splitter.setStretchFactor(0,0)
        self.splitter.setStretchFactor(1,0)
        self.splitter.setStretchFactor(2,10)
        self.splitter.setChildrenCollapsible(False)

        self.UI_layout.addWidget(self.splitter)
        #"""
        self.setStyleSheet('''
                 .QWidget{
                       background: white;
                       border: 1px solid #777;
                       border-right: white;
                       }
                 .QSplitter::handle{
                       background: white;
                       border-top: 1px solid #777;
                       border-bottom: 1px solid #777;
                       }
                           ''')

        #"""

    def change_widget(self,num):
        self.stack_layout.setCurrentIndex(num)

    def toggle_collapse(self):
        if self.collapsed:
            self.stack_widgets.show()
            self.collapsed = False
        else:
            self.stack_widgets.hide()
            self.collapsed = True

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
        #self.main_widget = QWidget(self)
        #self.main_layout = QHBoxLayout(self.main_widget)
        #self.main_widget.setLayout(self.main_layout)
        self.main_widget = QSplitter(self)
        # Add the sidetabwidget
        try:
            self.sidetabwidget = collapsibleSideTabs(self)
            #self.main_layout.addWidget(self.sidetabwidget)
            self.main_widget.addWidget(self.sidetabwidget)
        except:
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))
        
        
        self.sidetabwidget.tab_bar.tabBarDoubleClicked.connect(self.toggle_collapse)

        # Add the analysis tools tab widget
        self.analysistools_tabwidget = AnalysisTools_TabWidget(self)
        self.main_widget.addWidget(self.analysistools_tabwidget)

        #self.main_widget.setChildrenCollapsible(False)
        self.main_widget.setChildrenCollapsible(False)
        self.setCentralWidget(self.main_widget)
        
    def toggle_collapse(self):
        self.main_widget.setSizes([w.sizeHint().width() for w in [self.sidetabwidget,self.analysistools_tabwidget]])

if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()

    sys.exit(app.exec_())

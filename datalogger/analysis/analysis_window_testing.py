import sys,traceback

if __name__ == '__main__':
    sys.path.append('../')

from PyQt5.QtCore import QCoreApplication, QSize, Qt
from PyQt5.QtWidgets import (QWidget, QApplication, QTabWidget, QGridLayout, QHBoxLayout,
                             QMainWindow, QPushButton, QMouseEventTransition,
                             QTabBar, QSplitter,QStackedLayout,QLabel, QSizePolicy, QStackedWidget)
from PyQt5.QtGui import QPalette,QColor

from circle_fit import CircleFitWidget
from sonogram import SonogramWidget
from time_domain import TimeDomainWidget
from frequency_domain import FrequencyDomainWidget

import pyqtgraph as pg

from bin.channel import ChannelSet


class CollapsingSideTabWidget(QSplitter):
    def __init__(self, widget_side='left'):
        super().__init__()

        self.collapsed = False

        # # Create the tab bar
        self.tabBar = QTabBar()

        self.tabBar.setTabsClosable(False)
        self.tabBar.setMovable(False)

        # # Create the Stacked widget
        self.tabPages = QStackedWidget()

        # # Link the signals
        self.tabBar.tabBarDoubleClicked.connect(self.toggle_collapse)
        self.tabBar.currentChanged.connect(self.changePage)

        # # Add them to self
        if widget_side == 'left':
            self.tabBar.setShape(QTabBar.RoundedEast)
            self.addWidget(self.tabPages)
            self.addWidget(self.tabBar)
            self.setStretchFactor(0, 1)
            self.setStretchFactor(1, 0)
        if widget_side == 'right':
            self.tabBar.setShape(QTabBar.RoundedWest)
            self.addWidget(self.tabBar)
            self.addWidget(self.tabPages)
            self.setStretchFactor(0, 0)
            self.setStretchFactor(1, 1)

    def addTab(self, widget, title):
        self.tabBar.addTab(title)
        self.tabPages.addWidget(widget)

    def toggle_collapse(self):
        if self.collapsed:
            self.tabPages.show()
            self.collapsed = False
        else:
            self.tabPages.hide()
            self.collapsed = True

    def changePage(self, index):
        self.tabBar.setCurrentIndex(index)
        self.tabPages.setCurrentIndex(index)


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
        self.setWindowTitle('AnalysisWindow')

        self.init_ui()

        self.setFocus()
        self.show()

    def init_ui(self):
        # # Create the main widget
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        # Add the toolbox
        self.toolbox = CollapsingSideTabWidget()
        self.main_layout.addWidget(self.toolbox)

        self.toolbox.addTab(QLabel("Qwidget1"), "Page 1")
        self.toolbox.addTab(QLabel("Qwidget2"), "Page 2")

        # Add the analysis tools tab widget
        self.analysistools_tabwidget = AnalysisTools_TabWidget(self)
        self.main_layout.addWidget(self.analysistools_tabwidget)

        # Set the stretch factors
        self.main_layout.setStretchFactor(self.toolbox, 0)
        self.main_layout.setStretchFactor(self.analysistools_tabwidget, 1)



if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()

    sys.exit(app.exec_())

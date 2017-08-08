import sys

if __name__ == '__main__':
    sys.path.append('../')

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import (QWidget, QApplication, QTabWidget, QGridLayout,
                             QMainWindow)

from circle_fit import CircleFitWidget
from sonogram import SonogramWidget
from time_domain import TimeDomainWidget
from frequency_domain import FrequencyDomainWidget

import pyqtgraph as pg

from bin.channel import ChannelSet

class AnalysisTools_TabWidget(QTabWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setMovable(False)
        self.setTabsClosable(False)

        # # Create the tabs
        self.addTab(TimeDomainWidget(self), "Time Domain")
        self.addTab(FrequencyDomainWidget(self), "Frequency Domain")
        self.addTab(SonogramWidget(self), "Sonogram")
        self.addTab(CircleFitWidget(self), "Modal Fitting")


class AnalysisWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

        self.setFocus()
        self.showMaximized()

        self.cs = ChannelSet()

    def init_ui(self):
        # # Create a statusbar, menubar, and toolbar
        self.statusbar = self.statusBar()
        self.menubar = self.menuBar()
        self.toolbar = self.addToolBar("Tools")

        # # Set up the menu bar
        self.menubar.addMenu("Project")
        self.menubar.addMenu("Data")
        self.menubar.addMenu("View")
        self.menubar.addMenu("Addons")

        # #Create the main widget
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.main_layout = QGridLayout()
        self.main_widget.setLayout(self.main_layout)

        # Add the analysis tools tab widget
        self.main_layout.addWidget(AnalysisTools_TabWidget())

if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()

    sys.exit(app.exec_())

import sys

if __name__ == '__main__':
    sys.path.append('../')

from PyQt5.QtCore import QCoreApplication, QSize, Qt
from PyQt5.QtWidgets import (QWidget, QApplication, QTabWidget, QGridLayout, QHBoxLayout, QVBoxLayout,
                             QMainWindow, QPushButton, QMouseEventTransition, QTabBar, QSplitter)

from circle_fit import CircleFitWidget
from sonogram import SonogramWidget
from time_domain import TimeDomainWidget
from frequency_domain import FrequencyDomainWidget

import pyqtgraph as pg

from bin.channel import ChannelSet
from bin.file_import import import_from_mat

class SideTabWidget(QTabWidget):
    def __init__(self, widget_side='left'):
        super().__init__()

        self.setMinimumWidth(1)
        self.setMaximumWidth(100)

        self.setTabsClosable(False)
        self.setMovable(False)

        if widget_side == 'left':
            self.setTabPosition(QTabWidget.East)
        if widget_side == 'right':
            self.setTabPosition(QTabWidget.West)

class AnalysisTools_TabWidget(QTabWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()
        self.show()

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


        cs = ChannelSet()
        import_from_mat("//cued-fs/users/general/tab53/ts-home/Documents/owncloud/Documents/urop/labs/4c6/transfer_function_clean.mat", cs)

        self.analysistools_tabwidget.widget(3).transfer_function_type = 'acceleration'
        self.analysistools_tabwidget.widget(3).set_data(cs.get_channel_data(0, "omega"), cs.get_channel_data(0, "spectrum"))

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

        # # Create the main widget
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.main_layout = QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        # Add the sidetabwidget
        self.sidetabwidget = SideTabWidget('left')

        self.channel_page = QWidget()
        self.channel_page_layout = QVBoxLayout()
        self.channel_page.setLayout(self.channel_page_layout)
        self.sidetabwidget.addTab(self.channel_page, "Channels")

        page2 = QWidget()
        page2_layout = QGridLayout()
        page2.setLayout(page2_layout)

        self.sidetabwidget.addTab(page2, "Empty 2")
        self.main_layout.addWidget(self.sidetabwidget)

        # Add the analysis tools tab widget
        self.analysistools_tabwidget = AnalysisTools_TabWidget()
        self.main_layout.addWidget(self.analysistools_tabwidget)


if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()

    sys.exit(app.exec_())

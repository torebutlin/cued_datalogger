import sys,traceback

if __name__ == '__main__':
    sys.path.append('../')

from PyQt5.QtCore import QCoreApplication, QSize, Qt
from PyQt5.QtWidgets import (QWidget, QApplication, QTabWidget, QGridLayout, QHBoxLayout,
                             QMainWindow, QPushButton, QMouseEventTransition,
                             QTabBar, QSplitter,QStackedLayout,QLabel, QSizePolicy, QStackedWidget,
                             QVBoxLayout,QFormLayout,QGroupBox,QRadioButton,QButtonGroup,QComboBox,
                             QLineEdit,QAction,QMenu)
from PyQt5.QtGui import QPalette,QColor

from analysis.circle_fit import CircleFitWidget
from analysis.sonogram import SonogramWidget
from analysis.time_domain import TimeDomainWidget
from analysis.frequency_domain import FrequencyDomainWidget

import pyqtgraph as pg

from bin.channel import ChannelSet
from liveplotUI import DevConfigUI,ChanToggleUI


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

    def clear(self):
        for i in range(self.tabBar.count()):
            self.tabBar.removeTab(0)
            self.tabPages.removeWidget(self.tabPages.currentWidget())
        

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

        self.setGeometry(500,300,800,500)
        self.setWindowTitle('AnalysisWindow')
        
        
        self.prepare_tools()
        self.init_ui()

        self.setFocus()
        self.show()
        
    def prepare_tools(self):
        self.tools = []
        self.tools.append(TimeTools(self))
        self.tools.append(FreqTools(self))
        self.tools.append(ModalTools(self))
        
    def prepare_global_tools(self):
        self.global_toolbox = CollapsingSideTabWidget(widget_side='right')
        gtool = GlobalTools(self)
        for i in range(len(gtool)):
            self.global_toolbox.addTab(gtool.tool_pages[i],gtool.tabs_titles[i])
        
    def init_ui(self):
       
        menubar = self.menuBar()
        menubar.addMenu(ProjectMenu(self))
        
        # # Create the main widget
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        # Add the toolbox
        self.toolbox = CollapsingSideTabWidget()
        self.main_layout.addWidget(self.toolbox)

        # Add the analysis tools tab widget
        self.analysistools_tabwidget = AnalysisTools_TabWidget(self)
        self.main_layout.addWidget(self.analysistools_tabwidget)
                
        self.analysistools_tabwidget.currentChanged.connect(self.switch_tools)
        self.switch_tools(0)
        
        # Add the global tools tab widget
        self.prepare_global_tools()
        self.main_layout.addWidget(self.global_toolbox)

        # Set the stretch factors
        self.main_layout.setStretchFactor(self.toolbox, 0)
        self.main_layout.setStretchFactor(self.analysistools_tabwidget, 1)
        self.main_layout.setStretchFactor(self.global_toolbox, 0)
        
    def switch_tools(self,num):
        self.toolbox.clear()
        num = min(num,len(self.tools)-1)
        for i in range(len(self.tools[num])):
            self.toolbox.addTab(self.tools[num].tool_pages[i],
                                self.tools[num].tabs_titles[i])
            
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

        
        
class BaseTools():
    def __init__(self,parent):
        self.parent = parent
        self.tool_pages = []
        self.tabs_titles = []
        self.initTools()
        
    def __len__(self):
        return (len(self.tool_pages))
        
    def initTools(self):
        pass
    
    def add_tools(self,widget,name = None):
        self.tool_pages.append(widget)
        if name == None:
            name = 'Blank'
        self.tabs_titles.append(name)
        
class TimeTools(BaseTools):
    def initTools(self):
        convert_widget = QWidget()
        widget_layout = QVBoxLayout(convert_widget)
        fft_convert_btn = QPushButton('Calculate FFT', convert_widget)
        widget_layout.addWidget(fft_convert_btn)
        self.add_tools(convert_widget,'Conversion')

class FreqTools(BaseTools):
    def initTools(self):
        convert_widget = QWidget()
        widget_layout = QVBoxLayout(convert_widget)
        fft_convert_btn = QPushButton('Calculate Sonogram', convert_widget)
        widget_layout.addWidget(fft_convert_btn)
        self.add_tools(convert_widget,'Conversion')

class ModalTools(BaseTools):
    def initTools(self):
        convert_widget = QWidget()
        widget_layout = QVBoxLayout(convert_widget)
        fft_convert_btn = QPushButton('Transfer Function', convert_widget)
        widget_layout.addWidget(fft_convert_btn)
        self.add_tools(convert_widget,'Conversion')

class GlobalTools(BaseTools):
    def initTools(self):
        dev_configUI = DevConfigUI()
        dev_configUI.config_button.setText('Open Oscilloscope')
        self.add_tools(dev_configUI,'Oscilloscope')
        self.add_tools(ChanToggleUI(),'Channel Toggle')
        
if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()

    sys.exit(app.exec_())

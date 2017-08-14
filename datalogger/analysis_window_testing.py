import sys,traceback

if __name__ == '__main__':
    sys.path.append('../')

from PyQt5.QtCore import QCoreApplication, QSize, Qt,QTimer
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
import numpy as np

from bin.channel import ChannelSet
from liveplotUI import DevConfigUI,ChanToggleUI


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
        self.tabBar.tabBarDoubleClicked.connect(self.toggle_collapse)
        self.tabBar.currentChanged.connect(self.changePage)

        # # Add them to self
        if widget_side == 'left':
            self.tabBar.setShape(QTabBar.RoundedEast)
            self.addWidget(self.tabPages)
            self.addWidget(self.tabBar)
            #self.setStretchFactor(0, 1)
            #self.setStretchFactor(1, 0)
            self.addWidget(self.spacer)
            self.PAGE_IND = 0
            self.SPACE_IND = 2
        if widget_side == 'right':
            self.addWidget(self.spacer)
            self.tabBar.setShape(QTabBar.RoundedWest)
            self.addWidget(self.tabBar)
            self.addWidget(self.tabPages)
            #self.setStretchFactor(0, 0)
            #self.setStretchFactor(1, 1)
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
                sz[self.SPACE_IND] += sz[self.PAGE_IND] * 0.5
                sz[self.PAGE_IND] *= 0.5
            else:
                self.prev_sz = sz
                self.tabPages.hide()
                self.spacer.hide() 
                self.collapsetimer.stop()
        else:
            self.tabPages.show()
            sz = self.prev_sz
            if not sz[self.SPACE_IND] <5:
                sz[self.SPACE_IND] -= sz[self.PAGE_IND] * 0.5
                sz[self.PAGE_IND] *= 1.5
            else:
                self.tabPages.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred)
                self.spacer.hide() 
                self.collapsetimer.stop()   
        self.setSizes(sz)
        
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

        #self.prepare_tools()
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
        self.global_toolbox = CollapsingSideTabWidget('right')

        dev_configUI = DevConfigUI()
        dev_configUI.config_button.setText('Open Oscilloscope')

        self.global_toolbox.addTab(dev_configUI,'Oscilloscope')
        self.global_toolbox.addTab(ChanToggleUI(),'Channel Toggle')

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
        self.main_layout.addWidget(self.display_tabwidget)
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
        widget_layout = QHBoxLayout(convert_widget)
        fft_convert_btn = QPushButton('Calculate FFT', convert_widget)
        fft_convert_btn2 = QPushButton('Calculate FFT', convert_widget)
        widget_layout.addWidget(fft_convert_btn)
        widget_layout.addWidget(fft_convert_btn2)
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
        
        chan_toggle = QWidget()
        chan_toggle_layout = QVBoxLayout(chan_toggle)
        
        self.chantoggle_ui = ChanToggleUI()
        self.chantoggle_ui.toggle_ext_button.deleteLater()
        self.chantoggle_ui.chan_text.deleteLater()
        
        advtoggle_ui = AdvToggleUI()
        advtoggle_ui.close_ext_toggle.deleteLater()
         
        chan_toggle_layout.addWidget(self.chantoggle_ui)
        chan_toggle_layout.addWidget(advtoggle_ui)
        self.add_tools(chan_toggle,'Channel Toggle')
        
    def ResetChanBtns(self):
        for btn in self.chantoggle_ui.chan_btn_group.buttons():
            btn.setCheckState(Qt.Checked)
        
        n_buttons = self.chantoggle_ui.checkbox_layout.count()
        extra_btns = abs(len(self.parent.cs) - n_buttons)
        if extra_btns:
            if len(self.parent.cs) > n_buttons:
                columns_limit = 2
                current_y = (n_buttons-1)//columns_limit
                current_x = (n_buttons-1)%columns_limit
                for n in range(n_buttons,len(self.parent.cs)):
                    current_x +=1
                    if current_x%columns_limit == 0:
                        current_y +=1
                    current_x = current_x%columns_limit
                    
                    chan_btn = QCheckBox('Channel %i' % n,self.chantoggle_ui.channels_box)
                    chan_btn.setCheckState(Qt.Checked)
                    self.chantoggle_ui.checkbox_layout.addWidget(chan_btn,current_y,current_x)
                    self.chantoggle_ui.chan_btn_group.addButton(chan_btn,n)
            else:
                for n in range(n_buttons-1,len(self.parent.cs)-1,-1):
                    chan_btn = self.chantoggle_ui.chan_btn_group.button(n)
                    self.chantoggle_ui.checkbox_layout.removeWidget(chan_btn)
                    self.chantoggle_ui.chan_btn_group.removeButton(chan_btn)
                    chan_btn.deleteLater()
        
if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()

    sys.exit(app.exec_())

import sys,traceback

if __name__ == '__main__':
    sys.path.append('../')

from PyQt5.QtCore import QCoreApplication, QSize, Qt,QTimer
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

from bin.channel import ChannelSet
from liveplotUI import DevConfigUI,ChanToggleUI,AdvToggleUI


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
        
        self.timedomain_widget = TimeDomainWidget(self)
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
        self.prepare_channelsets()
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
        
        dev_configUI = DevConfigUI()
        dev_configUI.config_button.setText('Open Oscilloscope')
        self.gtools.addTab(dev_configUI,'Oscilloscope')
        
        
        chan_toggle = QWidget()
        chan_toggle_layout = QVBoxLayout(chan_toggle)
        self.chantoggle_ui = ChanToggleUI()
        self.chantoggle_ui.toggle_ext_button.deleteLater()
        self.chantoggle_ui.chan_text.deleteLater()
        advtoggle_ui = AdvToggleUI()
        advtoggle_ui.close_ext_toggle.deleteLater()
         
        chan_toggle_layout.addWidget(self.chantoggle_ui)
        chan_toggle_layout.addWidget(advtoggle_ui)
        self.gtools.addTab(chan_toggle,'Channel Toggle')  
        
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
        
        datas = self.cs.get_channel_data(tuple(range(3)),'t')
        self.plot_colours = ['r','g','b']
        self.timeplots = []
        for dt,p,i in zip(datas,self.plot_colours,range(len(self.cs))):
            self.timeplots.append(self.display_tabwidget.timedomain_widget.plotitem.plot(dt,pen = p))
            
        self.ResetChanBtns()
        self.chantoggle_ui.chan_btn_group.buttonClicked.connect(self.display_channel_plots)

        # Add the widgets
        self.main_layout.addWidget(self.toolbox)
        self.main_layout.addWidget(self.display_tabwidget)
        self.main_layout.addWidget(self.global_toolbox)
        # Set the stretch factors
        self.main_layout.setStretchFactor(self.toolbox, 0)
        self.main_layout.setStretchFactor(self.display_tabwidget, 1)
        self.main_layout.setStretchFactor(self.global_toolbox, 0)
        
    def prepare_channelsets(self):
        self.cs = ChannelSet(3)
        t = np.arange(1000)/44100
        y = np.sin(2*np.pi*1e3*t)
        self.cs.add_channel_dataset(0,'t',data=y)
        self.cs.add_channel_dataset(1,'t',data=y*np.sin(2*np.pi*10*t))
        self.cs.add_channel_dataset(2,'t',data=np.sign(y))
        
    def switch_tools(self,num):
        self.toolbox.clear()
        num = min(num,len(self.tools)-1)
        for i in range(len(self.tools[num])):
            self.toolbox.addTab(self.tools[num].tool_pages[i],
                                self.tools[num].tabs_titles[i])

    def display_channel_plots(self, btn):
        chan_num = self.chantoggle_ui.chan_btn_group.id(btn)
        if btn.isChecked():
            self.timeplots[chan_num].setPen(self.plot_colours[chan_num])
        else:
            self.timeplots[chan_num].setPen(None)
            
    def ResetChanBtns(self):
        for btn in self.chantoggle_ui.chan_btn_group.buttons():
            btn.setCheckState(Qt.Checked)
        
        n_buttons = self.chantoggle_ui.checkbox_layout.count()
        extra_btns = abs(len(self.cs) - n_buttons)
        if extra_btns:
            if len(self.cs) > n_buttons:
                columns_limit = 2
                current_y = (n_buttons-1)//columns_limit
                current_x = (n_buttons-1)%columns_limit
                for n in range(n_buttons,len(self.cs)):
                    current_x +=1
                    if current_x%columns_limit == 0:
                        current_y +=1
                    current_x = current_x%columns_limit
                    
                    chan_btn = QCheckBox('Channel %i' % n,self.chantoggle_ui.channels_box)
                    chan_btn.setCheckState(Qt.Checked)
                    self.chantoggle_ui.checkbox_layout.addWidget(chan_btn,current_y,current_x)
                    self.chantoggle_ui.chan_btn_group.addButton(chan_btn,n)
            else:
                for n in range(n_buttons-1,len(self.cs)-1,-1):
                    chan_btn = self.chantoggle_ui.chan_btn_group.button(n)
                    self.chantoggle_ui.checkbox_layout.removeWidget(chan_btn)
                    self.chantoggle_ui.chan_btn_group.removeButton(chan_btn)
                    chan_btn.deleteLater()
        
if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()

    sys.exit(app.exec_())

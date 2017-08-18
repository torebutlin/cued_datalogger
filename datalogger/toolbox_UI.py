# -*- coding: utf-8 -*-
"""
Created on Fri Aug 18 14:49:48 2017

@author: eyt21
"""
from PyQt5.QtCore import QCoreApplication, QSize, Qt,QTimer, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QApplication, QTabWidget, QGridLayout, QHBoxLayout,
                             QMainWindow, QPushButton, QMouseEventTransition,
                             QTabBar, QSplitter,QStackedLayout,QLabel, QSizePolicy, QStackedWidget,
                             QVBoxLayout,QFormLayout,QGroupBox,QRadioButton,QButtonGroup,QComboBox,
                             QLineEdit,QAction,QMenu, QCheckBox,QFileDialog)

COLLAPSE_FACTOR = 0.7

class CollapsingSideTabWidget(QSplitter):
    def __init__(self, widget_side='left',parent = None):
        super().__init__(parent)

        self.parent = parent
        self.collapsetimer = QTimer(self)
        self.collapsetimer.timeout.connect(self.update_splitter)

        #self.prev_sz = None

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
        self.parent.collapsed = not self.parent.collapsed
        sz = self.sizes()
        self.tabPages.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Ignored)
        sz[1] = self.tabBar.sizeHint().width()
        if self.parent.collapsed:
            sz[self.SPACE_IND] = 10
            sz[self.PAGE_IND] = 200
        else:
            self.tabPages.show()
            sz[self.PAGE_IND] = 10
            sz[self.SPACE_IND] = 200
        self.setSizes(sz)
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
        sz[1] = self.tabBar.sizeHint().width()
        if self.parent.collapsed:
            if not sz[self.PAGE_IND] < 5:
                sz[self.SPACE_IND] += sz[self.PAGE_IND] * COLLAPSE_FACTOR
                sz[self.PAGE_IND] *= COLLAPSE_FACTOR
            else:
                self.tabPages.hide()
                self.spacer.hide()
                self.collapsetimer.stop()
        else:
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
        
        self.collapsed = False
                #self.widget(i).toggle_collapse()
        #self.layout().setStackingMode(QStackedLayout.StackAll)

    def toggleCollapse(self):
        """Toggle collapse of all the widgets in the stack"""
        self.currentWidget().toggle_collapse()
        
    def show_toolbox(self,num):
        for i in range(self.count()):
            if not i == num:
                self.widget(i).tabPages.hide()
            
    def switch_toolbox(self,num):
        self.currentWidget().tabPages.hide()
        if not self.collapsed:
            self.widget(num).tabPages.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred)
            self.widget(num).tabPages.show()
        self.setCurrentIndex(num)
            
    def addToolbox(self, toolbox):
        """Add a toolbox to the stack"""
        toolbox.parent = self
        toolbox.setParent(self)
        toolbox.tabBar.tabBarDoubleClicked.connect(self.toggleCollapse)
        self.addWidget(toolbox)
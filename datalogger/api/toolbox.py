# -*- coding: utf-8 -*-
"""
Created on Fri Aug 18 14:49:48 2017

@author: eyt21
"""
from PyQt5.QtCore import QCoreApplication, QSize, Qt,QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import (QWidget, QApplication, QTabWidget, QGridLayout, QHBoxLayout,
                             QMainWindow, QPushButton, QMouseEventTransition,
                             QTabBar, QSplitter,QStackedLayout,QLabel, QSizePolicy, QStackedWidget,
                             QVBoxLayout,QFormLayout,QGroupBox,QRadioButton,QButtonGroup,QComboBox,
                             QLineEdit,QAction,QMenu, QCheckBox,QFileDialog)

COLLAPSE_FACTOR = 0.7

class Toolbox(QSplitter):
    """A side-oriented widget (like a TabWidget) that collapses when 
    the tabBar is double-clicked"""
    
    def __init__(self, widget_side='left', parent=None):
        self.parent = parent

        super().__init__(parent)
        
        self.setHandleWidth(0)
        self.setChildrenCollapsible(False)
               
        # # Create the tab bar
        self.tabBar = QTabBar(self)

        self.tabBar.setTabsClosable(False)
        self.tabBar.setMovable(False)

        # # Create the Stacked widget for the pages
        self.tabPages = QStackedWidget(self)
        
        # # Link the signals so that changing tab leads to a change of page
        self.tabBar.currentChanged.connect(self.changePage)

        # # Add them to the splitter (self)
        # Right side orientation
        if widget_side == 'right':
            self.tabBar.setShape(QTabBar.RoundedWest)

            self.addWidget(self.tabBar)
            self.addWidget(self.tabPages)
            #self.setStretchFactor(0, 1)
            #self.setStretchFactor(1, 0)
            
        # Left side orientation
        else:
            self.tabBar.setShape(QTabBar.RoundedEast)
            
            self.addWidget(self.tabPages)
            self.addWidget(self.tabBar)     
            #self.setStretchFactor(0, 1)
            #self.setStretchFactor(1, 0)
        
        # # Create the animation
        self.collapse_animation = QPropertyAnimation(self.tabPages, b'maximumWidth')
        self.collapse_animation.setDuration(250)
        self.collapse_animation.setEndValue(0)
        self.collapse_animation.finished.connect(self.on_animation_finished)
        
        self.collapsed = False
        self.max_width = 250
                
    def addTab(self, widget, title):
        """Add a new tab, with widget **widget** and title **title**"""
        self.tabBar.addTab(title)
        self.tabPages.addWidget(widget)
        
        if widget.sizeHint().width() >= self.max_width:
            self.max_width = widget.sizeHint().width()

    def toggle_collapse(self):
        """If collapsed, expand the widget so the pages are visible. If not 
        collapsed, collapse the widget so that only the tabBar is showing"""
        # If collapsed, expand
        if self.collapsed:
            self.expand()
        # If expanded, collapse:
        else:
            self.collapse()

    def on_animation_finished(self):
        if self.collapsed:
            self.tabPages.hide()
            
    def expand(self):
        self.collapse_animation.setStartValue(self.max_width)

        self.tabPages.show()
        self.collapse_animation.setDirection(QPropertyAnimation.Backward)
        self.collapse_animation.start()
        self.collapsed = False
    
    def collapse(self):
        self.collapse_animation.setStartValue(self.max_width)

        self.collapse_animation.setDirection(QPropertyAnimation.Forward)
        self.collapse_animation.start()
        self.collapsed = True
    
    def fast_collapse(self):
        self.tabPages.setMaximumWidth(0)
        self.tabPages.hide()
        self.collapsed = True
        
    def fast_expand(self):
        self.tabPages.setMaximumWidth(self.max_width)
        self.tabPages.show()
        self.collapsed = False

    def changePage(self, index):
        """Change page to **index**"""        
        self.tabBar.setCurrentIndex(index)
        self.tabPages.setCurrentIndex(index)
        
        self.tabPages.setMaximumWidth(self.max_width)
        
        if self.tabPages.currentWidget():
            self.tabPages.currentWidget().resize(self.max_width, 
                                                 self.tabPages.height())

    def clear(self):
        """Remove all tabs and pages"""
        for i in range(self.tabBar.count()):
            # Remove the tab and page at position 0
            self.tabBar.removeTab(0)
            self.tabPages.removeWidget(self.tabPages.currentWidget())


class MasterToolbox(QStackedWidget):
    """A Master Toolbox is a stack of CollapsingSideTabWidgets ('Toolboxes')"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        
    def toggle_collapse(self):
        """Toggle collapse of the Stack by toggle the collapse of the Toolbox
        that is on top."""
        self.currentWidget().toggle_collapse()

    def set_toolbox(self, toolbox_index):
        """Set current toolbox to toolbox given by **toolbox_index**"""
        # Save the old toolbox
        old_toolbox_collapsed = self.currentWidget().collapsed
        
        # Collapse and hide all other toolboxes
        for i in range(self.count()):
            if i == toolbox_index:
                continue
            else:
                self.widget(i).fast_collapse()
                self.widget(i).hide()
        
        # Collapse / Expand the toolbox
        if old_toolbox_collapsed:
            self.widget(toolbox_index).fast_collapse()
        else:
            self.widget(toolbox_index).fast_expand()
        
        # Set the current toolbox
        self.setCurrentIndex(toolbox_index)
            
            
    def add_toolbox(self, toolbox):
        """Add a Toolbox to the stack"""
        # Set the Toolbox's parent
        toolbox.parent = self
        toolbox.setParent(self)
        
        # When the Toolbox's tabBar is clicked, collapse the Toolbox
        toolbox.tabBar.tabBarDoubleClicked.connect(self.toggle_collapse)
        
        # Add the Toolbox to the stack
        self.addWidget(toolbox)
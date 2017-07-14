# -*- coding: utf-8 -*-
"""
Created on Tue Jul 11 11:44:12 2017

@author: eyt21
"""
import sys
from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QMainWindow,
    QPushButton, QApplication, QMessageBox, QDesktopWidget,QTabWidget,QTabBar)
#from PyQt5.QtGui import QIcon,QFont
from PyQt5.QtCore import QCoreApplication,QTimer

import numpy as np

import pyqtgraph as pg
import liveplotUI as lpUI
from wintabwidgets import data_tab_widget

from channel import Channel, ChannelSet

class DataWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set window parameter
        self.setGeometry(200,500,1000,500)
        self.setWindowTitle('DataWindow')

        # Construct UI        
        self.initUI()
        
        # Initialise the channels
        self.init_channels()
        
        # Center and show window
        self.center()
        self.setFocus()
        self.show()
     #------------- App construction methods--------------------------------     
    def initUI(self):
        # Set up the main widget to contain all Widgets
        self.main_widget = QWidget()
        # Set up the main layout
        vbox = QVBoxLayout(self.main_widget)
        
        # Set up the button to open the LivePlotting Window
        self.liveplot = None
        self.liveplotbtn = QPushButton('Open Oscilloscope',self.main_widget)
        self.liveplotbtn.resize(self.liveplotbtn.sizeHint())
        self.liveplotbtn.pressed.connect(self.toggle_liveplot)
        vbox.addWidget(self.liveplotbtn)
        
        
        #Set up the tabs container for recorded data
        self.data_tabs = QTabWidget(self)
        self.data_tabs.setMovable(True)
        self.data_tabs.setTabsClosable (True)
        #self.data_tabs.setTabPosition(0)
        vbox.addWidget(self.data_tabs)
        
        # Add tab containing a plot widget
        self.data_tabs.addTab(data_tab_widget(self), "Time Series")
        
        #Set the main widget as central widget
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
    
    # Center the window
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def init_channels(self):
        """Initialise the channels"""
        self.channel_set = ChannelSet()
            
    #------------- UI callback methods--------------------------------       
    def toggle_liveplot(self):
        if not self.liveplot:
            self.liveplot = lpUI.LiveplotApp(self)
            self.liveplot.show()
            self.liveplotbtn.setText('Close Oscilloscope')
            
            # Plot when data received
            self.liveplot.dataSaved.connect(self.plot_time_series)
            
        else:
            self.liveplot.close()
            self.liveplot = None
            self.liveplotbtn.setText('Open Oscilloscope')
    
    def plot_time_series(self):
        # Switch to time series tab
        self.data_tabs.setCurrentIndex(0)
        # Plot data
        self.data_tabs.currentWidget().canvasplot.plot((self.channel_set.channels[0].data, self.channel_set.channels[1].data), clear = True, pen='g')
        
    
    #----------------Overrding methods------------------------------------
    # The method to call when the mainWindow is being close       
    def closeEvent(self,event):
        reply = QMessageBox.question(self,'Message',
        'Are you sure you want to quit?', QMessageBox.Yes|
        QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.liveplot:
                self.liveplot.close()
            event.accept()
        else:
            event.ignore()
        
if __name__ == '__main__':
    app = 0 
    app = QApplication(sys.argv)
    w = DataWindow()
    sys.exit(app.exec_())
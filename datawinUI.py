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

import copy
import numpy as np

import pyqtgraph as pg
import liveplotUI as lpUI
from wintabwidgets import data_tab_widget
#import wintabwidgets as Tw

class DataWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set window parameter
        self.setGeometry(200,500,1000,500)
        self.setWindowTitle('DataWindow')

        # Construct UI        
        self.initUI()
        
        
        # Center and show window
        self.center()
        self.setFocus()
        self.show()
     #------------- App construction methods--------------------------------     
    def initUI(self):
        self.main_widget = QWidget()
        vbox = QVBoxLayout(self.main_widget)
        
        self.liveplot = None
        self.liveplotbtn = QPushButton('Open Oscilloscope',self.main_widget)
        self.liveplotbtn.resize(self.liveplotbtn.sizeHint())
        self.liveplotbtn.pressed.connect(self.toggle_liveplot)
        vbox.addWidget(self.liveplotbtn)
        
        self.data_tabs = QTabWidget(self)
        self.data_tabs.setMovable(True)
        self.data_tabs.setTabsClosable (True)
        self.data_tabs.setTabPosition (2)
        print(self.data_tabs.isMovable())
        vbox.addWidget(self.data_tabs)
        #self.current_tab = 0;
        # Setup the plot canvas
        '''self.tab_widgets = []        
        #self.add_tab_widget(Tw.data_tab_widget)
        self.tab_widgets.append(data_tab_widget(self))
        self.tab_widgets.append(QWidget())'''
        
        for i in range(2):
            self.data_tabs.addTab(data_tab_widget(self),'Tab %i' % (i))
        
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        #self.data_tabs.setFocus()
        #self.setCentralWidget(self.data_tabs)
        
    #def add_tab_widget(self,tab_type):
        
    
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
      
#------------- UI callback methods--------------------------------       
    def toggle_liveplot(self):
        if not self.liveplot:
            self.liveplot = lpUI.LiveplotApp(self)
            self.liveplot.show()
            self.liveplotbtn.setText('Close Oscilloscope')
        else:
            self.liveplot.close()
            self.liveplot = None
            self.liveplotbtn.setText('Open Oscilloscope')
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
    app = QApplication(sys.argv)
    w = DataWindow()
    sys.exit(app.exec_())
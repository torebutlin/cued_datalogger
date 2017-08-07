# -*- coding: utf-8 -*-
"""
Created on Tue Jul 11 13:41:44 2017

@author: eyt21
"""
from PyQt5.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton
import pyqtgraph as pg


# Widget for the tabs inside dataWindow
class data_tab_widget(QWidget):
    def __init__(self,parent):
        super().__init__()
        
        vbox = QVBoxLayout(self)
        
        # Set up data time plot
        self.canvas = pg.PlotWidget(self, background = 'default')
        vbox.addWidget(self.canvas)
        self.canvasplot = self.canvas.getPlotItem()
        #self.canvasplot.setLabels(title="Time Plot", bottom = 'Time(s)')
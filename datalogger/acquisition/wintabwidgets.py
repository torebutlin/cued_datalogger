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
        self.vb = self.canvas.getViewBox()
        print(self.canvasplot.scene())
        
        self.label = pg.LabelItem(angle = 0)
        self.label.setParentItem(self.vb)
        #self.vb.addItem(self.label)
        
        self.proxy = pg.SignalProxy(self.canvas.scene().sigMouseMoved, rateLimit=60, slot= self.mouseMoved)
        
    def mouseMoved(self,evt):
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.canvasplot.sceneBoundingRect().contains(pos):
            mousePoint = self.vb.mapSceneToView(pos)
            self.label.setText(("<span style='font-size: 12pt'>x=%0.4f,   <span style='color: red'>y1=%0.4f</span>" 
                                % (mousePoint.x(), mousePoint.y()) ))
        
    def closeEvent(self,event):
        self.proxy.disconnect()
        event.accept()
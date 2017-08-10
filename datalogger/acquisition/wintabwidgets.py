# -*- coding: utf-8 -*-
"""
Created on Tue Jul 11 13:41:44 2017

@author: eyt21
"""
from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,
                             QFormLayout)
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
        self.canvasplot.disableAutoRange()
        self.vb = self.canvas.getViewBox()
        self.vline = pg.InfiniteLine(angle=90)
        self.hline = pg.InfiniteLine(angle=0)
        self.canvasplot.addItem(self.vline)
        self.canvasplot.addItem(self.hline)
        
        self.label = pg.LabelItem(angle = 0)
        self.label.setParentItem(self.vb)
        #self.vb.addItem(self.label)
        
        self.proxy = pg.SignalProxy(self.canvas.scene().sigMouseMoved, rateLimit=60, slot= self.mouseMoved)
        
        form = QFormLayout()
        t1 = QLabel('XLimit',self)
        self.sp1 = pg.SpinBox(self)
        t2 = QLabel('YLimit',self)
        self.sp2 = pg.SpinBox(self)
        form.addRow(t1,self.sp1)
        form.addRow(t2,self.sp2)
        
        vbox.addLayout(form)
        
    def mouseMoved(self,evt):
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.canvasplot.sceneBoundingRect().contains(pos):
            mousePoint = self.vb.mapSceneToView(pos)
            self.label.setText(("<span style='font-size: 12pt'>x=%0.4f,   <span style='color: red'>y1=%0.4f</span>" 
                                % (mousePoint.x(), mousePoint.y()) ))
            self.vline.setPos(mousePoint.x())
            self.hline.setPos(mousePoint.y())
            
    def resetPlotWidget(self):
        self.canvasplot.clear()
        self.canvasplot.addItem(self.vline)
        self.canvasplot.addItem(self.hline)
        
        
    def closeEvent(self,event):
        self.proxy.disconnect()
        event.accept()
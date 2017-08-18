# -*- coding: utf-8 -*-
"""
Created on Tue Jul 11 13:41:44 2017

@author: eyt21
"""
from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,
                             QFormLayout)
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
import functools as fct
from datalogger.api.custom_plot import CustomPlotWidget

# Widget for the tabs inside dataWindow
class DataPlotWidget(QWidget):
    def __init__(self,parent):
        super().__init__()
        
        vbox = QVBoxLayout(self)
        
        # Set up data time plot
        self.canvas = CustomPlotWidget(self, background = 'default')
        vbox.addWidget(self.canvas)
        self.plotitem = self.canvas.getPlotItem()
        self.plotitem.disableAutoRange()
        self.vb = self.canvas.getViewBox()
        self.vline = pg.InfiniteLine(angle=90)
        self.hline = pg.InfiniteLine(angle=0)
        self.linregion = pg.LinearRegionItem(bounds = [0,None])
        self.linregion.sigRegionChanged.connect(self.checkRegion)
        self.resetPlotWidget()
        
        self.label = pg.LabelItem(angle = 0)
        self.label.setParentItem(self.vb)
        #self.vb.addItem(self.label)
        
        self.proxy = pg.SignalProxy(self.canvas.scene().sigMouseMoved, rateLimit=60, slot= self.mouseMoved)
        
        ui_layout = QHBoxLayout()
        t1 = QLabel('Lower',self)
        self.sp1 = pg.SpinBox(self,bounds = (0,None))
        t2 = QLabel('Upper',self)
        self.sp2 = pg.SpinBox(self,bounds = (0,None))
        self.zoom_btn = QPushButton('Zoom',self)
        ui_layout.addWidget(t1)
        ui_layout.addWidget(self.sp1)
        ui_layout.addWidget(t2)
        ui_layout.addWidget(self.sp2)
        ui_layout.addWidget(self.zoom_btn)
        
        
        self.zoom_btn.clicked.connect(self.zoomToRegion)
        vbox.addLayout(ui_layout)
        
        self.updatetimer = QTimer(self)
        self.updatetimer.timeout.connect(self.updateRegion)
        self.updatetimer.start(20)
        
    def mouseMoved(self,evt):
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.plotitem.sceneBoundingRect().contains(pos):
            mousePoint = self.vb.mapSceneToView(pos)
            self.label.setText(("<span style='font-size: 12pt;color: black'>x=%0.4f,   <span style='color: red'>y1=%0.4f</span>" 
                                % (mousePoint.x(), mousePoint.y()) ))
            self.vline.setPos(mousePoint.x())
            self.hline.setPos(mousePoint.y())
            
    def resetPlotWidget(self):
        self.plotitem.clear()
        self.plotitem.addItem(self.vline)
        self.plotitem.addItem(self.hline)
        self.plotitem.addItem(self.linregion)
        
    def updateRegion(self):
        pos = [self.sp1.value(),self.sp2.value()]
        pos.sort()
        self.linregion.setRegion(pos)
        self.sp1.setValue(pos[0])
        self.sp2.setValue(pos[1])
        
    def checkRegion(self):
        pos = list(self.linregion.getRegion())
        pos.sort()
        self.sp1.setValue(pos[0])
        self.sp2.setValue(pos[1])
        
    def zoomToRegion(self):
        pos = self.linregion.getRegion()
        self.plotitem.setXRange(pos[0],pos[1],padding = 0.1)
        
        
    def closeEvent(self,event):
        self.proxy.disconnect()
        if self.updatetimer.isActive():
            self.updatetimer.stop()
        event.accept()
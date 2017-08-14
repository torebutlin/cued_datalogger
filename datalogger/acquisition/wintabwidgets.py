# -*- coding: utf-8 -*-
"""
Created on Tue Jul 11 13:41:44 2017

@author: eyt21
"""
from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,
                             QFormLayout)
import pyqtgraph as pg
import functools as fct

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
        self.linregion = pg.LinearRegionItem(values = [0.4,0.6],bounds = [0,None])
        self.linregion.sigRegionChanged.connect(self.checkRegion)
        self.resetPlotWidget()
        
        self.label = pg.LabelItem(angle = 0)
        self.label.setParentItem(self.vb)
        #self.vb.addItem(self.label)
        
        self.proxy = pg.SignalProxy(self.canvas.scene().sigMouseMoved, rateLimit=60, slot= self.mouseMoved)
        
        ui_layout = QHBoxLayout()
        t1 = QLabel('XLimit',self)
        self.sp1 = pg.SpinBox(self)
        t2 = QLabel('YLimit',self)
        self.sp2 = pg.SpinBox(self)
        self.zoom_btn = QPushButton(self)
        ui_layout.addWidget(t1)
        ui_layout.addWidget(self.sp1)
        ui_layout.addWidget(t2)
        ui_layout.addWidget(self.sp2)
        ui_layout.addWidget(self.zoom_btn)
        
        self.sp1.sigValueChanging.connect(self.updateRegion)
        self.sp2.sigValueChanging.connect(self.updateRegion)
        self.zoom_btn.clicked.connect(self.zoomToRegion)
        vbox.addLayout(ui_layout)
        
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
        self.canvasplot.addItem(self.linregion)
        
    def updateRegion(self):
        pos = [self.sp1.value(),self.sp2.value()]
        pos.sort()
        self.linregion.setRegion(pos)
        self.sp1.setValue(pos[0])
        self.sp2.setValue(pos[1])
        
    def checkRegion(self):
        pos = list(self.linregion.getRegion())
        pos.sort()
        self.linregion.setRegion(pos)
        self.sp1.setValue(pos[0])
        self.sp2.setValue(pos[1])
        
    def zoomToRegion(self):
        pos = self.linregion.getRegion()
        self.canvasplot.setXRange(pos[0],pos[1],padding = 0.1)
        
        
    def closeEvent(self,event):
        self.proxy.disconnect()
        event.accept()
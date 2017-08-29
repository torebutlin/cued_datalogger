# -*- coding: utf-8 -*-
"""
Created on Thu Aug 24 17:35:00 2017

@author: eyt21
"""
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, pyqtSignal 

from datalogger.api.pyqtgraph_extensions import CustomPlotWidget

import pyqtgraph as pg
import numpy as np
import math

CHANLVL_FACTOR = 0.1# The gap between each channel level (seems useless)
TRACE_DECAY = 0.005 # Increment size for decaying trace
TRACE_DURATION = 2  # Duration for a holding trace

class LiveGraph(pg.PlotWidget):
    plotLineClicked = pyqtSignal()
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.plotlines = []
        self.plot_xoffset = []
        self.plot_yoffset = []
        self.plot_colours = []
        self.plotItem = self.getPlotItem()
        self.gen_default_colour()
        
    def plot(self, *arg, **kwargs):
        line = self.plotItem.plot(*arg, **kwargs)
        line.curve.setClickable(True,width = 4)
        self.plotlines.append(line)
        return line
        
    def check_line(self,line):
        if line in self.plotlines:
            return self.plotlines.index(line)
        else:
            return None
        
    def toggle_plotline(self,num,visible):
        if visible:
            self.plotlines[num].setPen(self.plot_colours[num])
        else:
            self.plotlines[num].setPen(None)
            
    def set_plot_colour(self,num,col,drawnow = False):
        self.plot_colours[num] = col
        if drawnow:
            self.plotlines[num].setPen(col)
        
    def set_offset(self,num,x_off = None, y_off =None):
        if not x_off is None:
            self.plot_xoffset[num] = x_off
        if not y_off is None:
            self.plot_yoffset[num] = y_off
    
    def update_line(self,num, *arg,x = None,y = None, **kwargs):
        self.plotlines[num].setData(*arg,x = x+self.plot_xoffset[num],
                      y = y+ self.plot_yoffset[num],**kwargs)
        
    def reset_plotlines(self):
        for _ in range(len(self.plotlines)):
            line = self.plotlines.pop()
            line.clear()
            del line
            
    def reset_offsets(self):
        n = len(self.plotlines)
        self.plot_xoffset = np.zeros(shape = (n,), dtype = np.float)
        self.plot_yoffset = np.arange(n, dtype = np.float)
        
    def reset_colour(self):
        self.plot_colours = [None] * len(self.plotlines)
        self.gen_default_colour()
        
    def reset_default_colour(self,chan,drawnow):
        col = self.def_colours[chan]
        self.set_plot_colour(chan,col,drawnow = drawnow)
        return col
    
    def gen_default_colour(self):
        val = [0.0,0.5,1.0]
        colour = np.array([[255,0,0,255],[0,255,0,255],[0,0,255,255]], dtype = np.ubyte)
        self.plot_colourmap =  pg.ColorMap(val,colour)
        c_list = self.plot_colourmap.getLookupTable(nPts = len(self.plotlines))
        
        self.def_colours = []
        for i in range(len(self.plotlines)):
            r,g,b = c_list[i]
            self.set_plot_colour(i,QColor(r,g,b),True)
            self.def_colours.append(QColor(r,g,b))
    
class TimeLiveGraph(LiveGraph):
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
        self.sig_hold = []
        self.plotItem.setLabels(title="Time Plot", bottom = 'Time(s)') 
        
    def set_sig_hold(self, num, state):
        self.sig_hold[num] = state
    
    def reset_sig_hold(self):
        self.sig_hold = [Qt.Unchecked] * len(self.plotlines)
        

class FreqLiveGraph(LiveGraph):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.plotItem.setLabels(title="FFT Plot", bottom = 'Freq(Hz)')
        self.plotItem.disableAutoRange(axis=None)
        

class LevelsLiveGraph(LiveGraph):
    thresholdChanged = pyqtSignal(str)
    def __init__(self,rec,*args,**kwargs):
        self.peak_plots = []
        self.peak_trace = []
        self.trace_counter = []
        self.trace_countlimit = 30
        self.level_colourmap = None
        
        super().__init__(*args,**kwargs)
        self.plotItem.setLabels(title="Channel Levels", bottom = 'Amplitude')
        self.plotItem.hideAxis('left')
        
        self.chanlvl_pts = self.plotItem.plot()
        
        
        
        self.chanlvl_bars = pg.ErrorBarItem(x=np.arange(rec.channels),
                                            y =np.arange(rec.channels)*0.1,
                                            beam = CHANLVL_FACTOR/2,
                                            pen = pg.mkPen(width = 3))
        
        self.plotItem.addItem(self.chanlvl_bars)
        
        baseline = pg.InfiniteLine(pos = 0.0, movable = False)
        self.plotItem.addItem(baseline)
        
        self.threshold_line = pg.InfiniteLine(pos = 0.0, movable = True,bounds = [0,1])
        self.threshold_line.sigPositionChanged.connect(self.change_threshold)
        self.plotItem.addItem(self.threshold_line)
        
        self.reset_channel_peaks(rec)
        
        val = [0.0,0.1,0.2]
        colour = np.array([[0,255,0,255],[0,255,0,255],[255,0,0,255]], dtype = np.ubyte)
        self.level_colourmap = pg.ColorMap(val,colour)
     
        
    def set_plot_colour(self,num,col,drawnow = False):
        self.plot_colours[num] = col
        self.chanlvl_pts.scatter.setBrush(col)
        
    def set_peaks(self,num,maximum):
        if self.trace_counter[num]>self.trace_countlimit:
            self.peak_trace[num] = max(self.peak_trace[num]*math.exp(-self.peak_decays[num]),0)
            self.peak_decays[num] += TRACE_DECAY
        self.trace_counter[num] += 1
        
        if self.peak_trace[num]<maximum:
            self.peak_trace[num] = maximum
            self.peak_decays[num] = 0
            self.trace_counter[num] = 0
            
        self.peak_plots[num].setData(x = [self.peak_trace[num],self.peak_trace[num]],
                       y = [(num-0.3), (num+0.3)])
        
        self.peak_plots[num].setPen(self.level_colourmap.map(self.peak_trace[num]))
        
    def set_channel_levels(self,value,maximum):
        self.chanlvl_bars.setData(x = value,y = np.arange(len(self.peak_plots)), right = maximum-value,left = value)
        self.chanlvl_pts.setData(x = value,y = np.arange(len(self.peak_plots)))
        
    def change_threshold(self,arg):
        if type(arg) == str:
            self.threshold_line.setValue(float(arg))
        else:
            self.thresholdChanged.emit('%.2f' % arg.value())
    
    def reset_colour(self):
        self.plot_colours = [None] * len(self.peak_plots)
        self.gen_default_colour()
        
    def reset_default_colour(self,chan,drawnow):
        col = self.def_colours[chan]
        self.set_plot_colour(chan,col)
        return col
        
    def gen_default_colour(self):
        val = [0.0,0.5,1.0]
        colour = np.array([[255,0,0,255],[0,255,0,255],[0,0,255,255]], dtype = np.ubyte)
        plot_colourmap =  pg.ColorMap(val,colour)
        c_list = plot_colourmap.getLookupTable(nPts = len(self.peak_plots))
        
        self.def_colours = []
        for i in range(len(self.peak_plots)):
            r,g,b = c_list[i]
            #self.plotlines.set_plot_colour(i,QColor(r,g,b),True)
            self.plot_colours[i] = QColor(r,g,b)
            self.def_colours.append(QColor(r,g,b))
        
    def reset_channel_levels(self):
        self.chanlvl_pts.clear()
        self.chanlvl_pts = self.plotItem.plot(pen = None,symbol='o',
                                                  symbolBrush = self.plot_colours,
                                                  symbolPen = None)
        
    def reset_channel_peaks(self,rec):
        for _ in range(len(self.peak_plots)):
            line = self.peak_plots.pop()
            line.clear()
            del line
        
        self.peak_trace = np.zeros(rec.channels)
        self.peak_decays = np.zeros(rec.channels)
        self.trace_counter = np.zeros(rec.channels)
        self.trace_countlimit = TRACE_DURATION *rec.rate//rec.chunk_size  
        
        self.threshold_line.setBounds((0,rec.max_value))
        
        for i in range(rec.channels):
            self.peak_plots.append(self.plotItem.plot(x = [self.peak_trace[i],self.peak_trace[i]],
                                                          y = [(i-0.3), (i+0.3)])) 
        
        
        self.plotItem.setRange(xRange = (0,rec.max_value+0.1),yRange = (-0.5, (rec.channels+5-0.5)))
        self.plotItem.setLimits(xMin = -0.1,xMax = rec.max_value+0.1,yMin = -0.5,yMax = (rec.channels+5-0.5))
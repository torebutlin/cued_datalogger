# -*- coding: utf-8 -*-
"""
Created on Thu Aug 24 17:35:00 2017

@author: eyt21

This module contains the live graph classes to the acquisition window.

Attribute
----------
CHANLVL_FACTOR: float
    Not used
TRACE_DECAY: float
    The decay factor of the peak plots
TRACE_DURATION: float
    Duration before the peak plots decay
"""
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, pyqtSignal 

from datalogger.api.pyqtgraph_extensions import CustomPlotWidget

import pyqtgraph as pg
import numpy as np
import math

CHANLVL_FACTOR = 0.1
TRACE_DECAY = 0.005
TRACE_DURATION = 2.0

class LiveGraph(pg.PlotWidget):
    """
    A base PlotWidget reimplemented to store extra plot information, such as
    offsets, colours, and visibility.
    
    Attributes
    ----------
    plotColourChanged: pyqtsignal
        Emits when colour of a plot change
        Sends out QColor
    plotlines: list of PlotDataItem
        Contains the individual PlotDataItem
    plot_xoffset: list of float
        Contains the X offset of each plot
    plot_yoffset: list of float
        Contains the Y offset of each plot
    plot_colours:list of QColor
        Contains the current colour of each plot
    plot_visible: list of bool
        Contains the visibility of each plot
    """
    #plotLineClicked = pyqtSignal()
    plotColourChanged = pyqtSignal(object)
    def __init__(self,*args,**kwargs):
        """
        Reimplemented PlotWidget
        Set the background black and axes white
        All parameters are passed into PlotWidget
        """
        super().__init__(*args,background = 'k',**kwargs)
        self.plotlines = []
        self.plot_xoffset = []
        self.plot_yoffset = []
        self.plot_colours = []
        self.plot_visible = []
        self.plotItem = self.getPlotItem()
        self.gen_default_colour()
        
        self.plotItem.getAxis('bottom').setPen('w') 
        self.plotItem.getAxis('left').setPen('w')
        
    def plot(self, *arg, **kwargs):
        """
        Plot the data and set it to be clickable
        
        Return
        ----------
        PlotDataItem
            The plot line, effectively
        """
        line = self.plotItem.plot(*arg, **kwargs)
        line.curve.setClickable(True,width = 4)
        self.plotlines.append(line)
        return line
        
    def check_line(self,line):
        """
        Check whether a plot line exists
        
        Return
        ----------
        int
            Index of the plot line, if it exists
            None otherwise
        """
        if line in self.plotlines:
            return self.plotlines.index(line)
        else:
            return None
    
    def toggle_plotline(self,num,visible):
        """
        Set the visibility of the specific line
        
        Parameters
        ----------
        num: int
            index of the line to be set
        visible: bool
            Visibility of the line to be set
        """
        self.plot_visible[num] = visible
        if visible:
            self.plotlines[num].setPen(self.plot_colours[num])
        else:
            self.plotlines[num].setPen(None)
            
    def set_plot_colour(self,num,col):
        """
        Set the colour of the specific line
        
        Parameters
        ----------
        num: int
            index of the line to be set
        col: QColor
            Colour of the line to be set
        """
        self.plot_colours[num] = col
        if self.plot_visible[num]:
            self.plotlines[num].setPen(col)
        
    def set_offset(self,num,x_off = None, y_off =None):
        """
        Set the offsets of the specific line
        
        Parameters
        ----------
        num: int
            index of the line to be set
        x_off: float
            X offset of the line to be set, if given a value
        x_off: float
            Y offset of the line to be set, if given a value
        """
        if not x_off is None:
            self.plot_xoffset[num] = x_off
        if not y_off is None:
            self.plot_yoffset[num] = y_off
    
    def update_line(self,num, *arg,x = None,y = None, **kwargs):
        """
        Update the existing lines with new data, with the offsets
        
        Parameters
        ----------
        num: int
            index of the line to be set
        x: float
            X data of the line to be set, if given a value
        y: float
            Y data of the line to be set, if given a value
        The rest to pass to PlotDataItem.setData
        """
        self.plotlines[num].setData(*arg,x = x+self.plot_xoffset[num],
                      y = y+ self.plot_yoffset[num],**kwargs)
        
    def reset_plotlines(self):
        """
        Clear all of the lines
        """
        for _ in range(len(self.plotlines)):
            line = self.plotlines.pop()
            line.clear()
            del line
            
    def reset_offsets(self):
        """
        Reset the offsets of the plots
        """
        n = len(self.plotlines)
        self.plot_xoffset = np.zeros(shape = (n,), dtype = np.float)
        self.plot_yoffset = np.arange(n, dtype = np.float)
        
    def reset_plot_visible(self):
        """
        Reset the visibilities of the plots
        """
        self.plot_visible = [True]*len(self.plotlines)
            
    def reset_colour(self):
        """
        Clear the colours of the plots
        """
        self.plot_colours = [None] * len(self.plotlines)
        self.gen_default_colour()
        
    def reset_default_colour(self,num):
        """
        Set the default colour of the specified plot
        Parameters
        ----------
        num: int
            Index of the line to be set
        """
        col = self.def_colours[num]
        self.set_plot_colour(num,col)
        self.plotColourChanged.emit(col)
        #return col
    
    def gen_default_colour(self):
        """
        Generate the default colours of the plots
        """
        val = [0.0,0.5,1.0]
        colour = np.array([[255,0,0,255],[0,255,0,255],[0,0,255,255]], dtype = np.ubyte)
        self.plot_colourmap =  pg.ColorMap(val,colour)
        c_list = self.plot_colourmap.getLookupTable(nPts = len(self.plotlines))
        
        self.def_colours = []
        for i in range(len(self.plotlines)):
            r,g,b = c_list[i]
            self.set_plot_colour(i,QColor(r,g,b))
            self.def_colours.append(QColor(r,g,b))
    
class TimeLiveGraph(LiveGraph):
    """
    Reimplemented LiveGraph. Displays the time domain plot
    
    Attributes
    ----------
    sig_hold: list of bool
        Contains whether the signal is being held
    """
    def __init__(self, *args,**kwargs):
        """
        Reimplemented from LiveGraph.
        """
        super().__init__(*args,**kwargs)
        self.sig_hold = []
        self.plotItem.setTitle(title="Time Plot", color = 'FFFFFF')
        self.plotItem.setLabel('bottom','Time(s)')
        
    def set_sig_hold(self, num, state):
        """
        Set the hold status of the specific line
        
        Parameters
        ----------
        num: int
            Index of the line to be set
        state: bool
            Hold status of the line to be set
        """
        self.sig_hold[num] = state
    
    def reset_sig_hold(self):
        self.sig_hold = [Qt.Unchecked] * len(self.plotlines)

class FreqLiveGraph(LiveGraph):
    """
    Reimplemented LiveGraph. Displays the frequency domain plot
    """
    def __init__(self,*args,**kwargs):
        """
        Reimplemented from LiveGraph.
        """
        super().__init__(*args,**kwargs)
        self.plotItem.setTitle(title="FFT Plot", color = 'FFFFFF')
        self.plotItem.setLabel('bottom','Freq(Hz)')
        self.plotItem.disableAutoRange(axis=None)
        

class LevelsLiveGraph(LiveGraph):
    """
    Reimplemented LiveGraph. Displays the channel levels
    
    Attributes
    ----------
    thresholdChanged: pyqtSignal
        Emits when the threshold line is moved
        Sends out the value of the threshold
    peak_plots: list of plotDataItem
        The lines which indicate the channels' peaks
    peak_trace: list of float
        The values of the channels' peaks
    trace_counter: list of int
        Counter for the peak plots before they decay
    chanlvl_pts: list of plotDataItem
        Rms plots
    chanlvl_bars: list of bool
        Instantaneous channels' peaks plots
    threshold_line:
        The line indicating the trigger threshold
    level_colourmap:
        The colour for the peak levels
    """
    thresholdChanged = pyqtSignal(str)
    def __init__(self,rec,*args,**kwargs):
        """
        Reimplemented from LiveGraph.
        
        Parameters
        ----------
        rec: Recorder
            The reference of the Recorder
        The rest are passed into LiveGraph
        """
        self.peak_plots = []
        self.peak_trace = []
        self.trace_counter = []
        self.trace_countlimit = 30
        self.level_colourmap = None
        
        super().__init__(*args,**kwargs)
        self.plotItem.setTitle(title="Channel Levels", color = 'FFFFFF')
        self.plotItem.setLabel('bottom','Amplitude')
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
        
        val = [0.0,0.5,0.8]
        colour = np.array([[0,255,0,255],[0,255,0,255],[255,0,0,255]], dtype = np.ubyte)
        self.level_colourmap = pg.ColorMap(val,colour)
        
    def set_plot_colour(self,num,col):
        """        
        Parameters
        ----------
        num: int
            index of the point to be set
        col: QColor
            Colour of the point to be set
        """
        self.plot_colours[num] = col
        self.chanlvl_pts.scatter.setBrush(col)
        
    def set_peaks(self,num,maximum):
        """
        Set the value of the peak plots
        Parameters
        ----------
        num: int
            index of the peak to be set
        maximum: float
            Instantaneous maximum value of the peak
        """
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
        """
        Set the value of the levels plots
        Parameters
        ----------
        value: float
            rms values
        maximum: float
            Instantaneous maximum value of the plot
        """
        self.chanlvl_bars.setData(x = value,y = np.arange(len(self.peak_plots)), right = maximum-value,left = value)
        self.chanlvl_pts.setData(x = value,y = np.arange(len(self.peak_plots)))
        
    def change_threshold(self,arg):
        """
        Set the trigger threshold
        If arg is str, set the threshold_line to match the value
        otherwise, emit the value of the threshold_line
        
        Parameters
        ----------
        arg: str or InfiniteLine
        """
        if type(arg) == str:
            self.threshold_line.setValue(float(arg))
        else:
            self.thresholdChanged.emit('%.2f' % arg.value())
    
    def reset_colour(self):
        """
        Reimplemented from LiveGraph.
        """
        self.plot_colours = [None] * len(self.peak_plots)
        self.gen_default_colour()
        
    def reset_default_colour(self,chan):
        """
        Reimplemented from LiveGraph.
        """
        col = self.def_colours[chan]
        self.set_plot_colour(chan,col)
        return col
        
    def gen_default_colour(self):
        """
        Reimplemented from LiveGraph.
        """
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
        """
        Reset the channel levels plot
        """
        self.chanlvl_pts.clear()
        self.chanlvl_pts = self.plotItem.plot(pen = None,symbol='o',
                                                  symbolBrush = self.plot_colours,
                                                  symbolPen = None)
        
    def reset_channel_peaks(self,rec):
        """
        Reset the channel peaks plot
        """
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
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 24 17:35:00 2017

@author: eyt21
"""

from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QMainWindow,
    QPushButton, QDesktopWidget,QStatusBar, QLabel,QLineEdit, QFormLayout,
    QGroupBox,QRadioButton,QSplitter,QFrame, QComboBox,QScrollArea,QGridLayout,
    QCheckBox,QButtonGroup,QTextEdit,QApplication,QStackedLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint 
import pyqtgraph as pg
import numpy as np

CHANLVL_FACTOR = 0.1# The gap between each channel level (seems useless)

class LiveGraph(pg.PlotWidget):
    plotLineClicked = pyqtSignal()
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.plotlines = []
        self.plot_xoffset = []
        self.plot_yoffset = []
        self.plot_colours = []
        self.plotItem = self.getPlotItem()
        
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

class LevelsLiveGraph(QWidget):
    def __init__(self):
        chanlevel_UI = QWidget(self.right_splitter)
        chanlevel_UI_layout = QVBoxLayout(chanlevel_UI)
        self.chanelvlcvs = pg.PlotWidget(self.right_splitter, background = 'default')
        chanlevel_UI_layout.addWidget(self.chanelvlcvs)
        
        self.channelvlplot = self.chanelvlcvs.getPlotItem()
        self.channelvlplot.setLabels(title="Channel Levels", bottom = 'Amplitude')
        self.channelvlplot.hideAxis('left')
        self.chanlvl_pts = self.channelvlplot.plot()
        
        self.peak_plots = []
        
        self.chanlvl_bars = pg.ErrorBarItem(x=np.arange(self.rec.channels),
                                            y =np.arange(self.rec.channels)*0.1,
                                            beam = CHANLVL_FACTOR/2,
                                            pen = pg.mkPen(width = 3))
        
        self.channelvlplot.addItem(self.chanlvl_bars)
        
        baseline = pg.InfiniteLine(pos = 0.0, movable = False)
        self.channelvlplot.addItem(baseline)
        
        self.threshold_line = pg.InfiniteLine(pos = 0.0, movable = True,bounds = [0,1])
        self.threshold_line.sigPositionChanged.connect(self.change_threshold)
        self.channelvlplot.addItem(self.threshold_line)
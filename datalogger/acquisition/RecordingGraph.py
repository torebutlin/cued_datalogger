# -*- coding: utf-8 -*-
"""
Created on Thu Aug 24 17:35:00 2017

@author: eyt21
"""

from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QMainWindow,
    QPushButton, QDesktopWidget,QStatusBar, QLabel,QLineEdit, QFormLayout,
    QGroupBox,QRadioButton,QSplitter,QFrame, QComboBox,QScrollArea,QGridLayout,
    QCheckBox,QButtonGroup,QTextEdit,QApplication,QStackedLayout)

import pyqtgraph as pg
import numpy as np

CHANLVL_FACTOR = 0.1# The gap between each channel level (seems useless)

class TimeLiveGraph(QWidget):
    def __init__(self):
        self.timeplotcanvas = pg.PlotWidget(self.mid_splitter)
        self.timeplot = self.timeplotcanvas.getPlotItem()
        self.timeplot.setLabels(title="Time Plot", bottom = 'Time(s)') 

class FreqLiveGraph(QWidget):
    def __init__(self):
        self.fftplotcanvas = pg.PlotWidget(self.mid_splitter)
        self.fftplot = self.fftplotcanvas.getPlotItem()
        self.fftplot.setLabels(title="FFT Plot", bottom = 'Freq(Hz)')
        self.fftplot.disableAutoRange(axis=None)

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
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  5 13:12:34 2017

@author: eyt21
"""
import sys
from PyQt5.QtWidgets import (QWidget, QToolTip,QVBoxLayout,QMainWindow,
    QPushButton, QApplication, QMessageBox, QDesktopWidget,QSizePolicy)
#from PyQt5.QtGui import QIcon,QFont
from PyQt5.QtCore import QCoreApplication,QTimer

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

import pyqtgraph as pg
import myRecorder as rcd

#--------------------- The App Class------------------------------------
class Example(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set window parameter
        self.setGeometry(500,500,500,500)
        self.setWindowTitle('LiveStreamPlot')
        
        # Set recorder object
        self.rec = rcd.Recorder(num_chunk = 6,
                                device_name = 'Line (U24XL with SPDIF I/O)')
        self.rec.stream_init(playback = True)
        self.playing = True
        
        # Construct UI        
        self.initUI()
        
        # Center and show window
        self.center()
        self.setFocus()
        self.show()
     #------------- App construction methods--------------------------------     
    def initUI(self):
        # Setup the plot canvas        
        self.main_widget = QWidget(self)
        vbox = QVBoxLayout(self.main_widget)
        
        # Set up time domain plot
        self.timeplotcanvas = pg.PlotWidget(self.main_widget, background = 'default')
        vbox.addWidget(self.timeplotcanvas)
        self.timeplot = self.timeplotcanvas.getPlotItem()
        self.timeplot.setLabels(title="Time Plot")
        self.timeplot.disableAutoRange(axis=None)
        self.timeplot.setRange(xRange = (0,1024*6),yRange = (-2**15, 2**15))
        self.timeplotline = self.timeplot.plot(pen='g')
        
        # Set up PSD plot
        self.fftplotcanvas = pg.PlotWidget(self.main_widget, background = 'default')
        vbox.addWidget(self.fftplotcanvas)
        self.fftplot = self.fftplotcanvas.getPlotItem()
        self.fftplot.setLabels(title="PSD Plot")
        self.fftplot.disableAutoRange(axis=None)
        self.fftplot.setRange(xRange = (0,1024*6/2),yRange = (0, 2**15))
        self.fftplotline = self.fftplot.plot(pen = 'y')
        
        self.update_line()
        
        # Set up the button
        btn = QPushButton('Switch',self.main_widget)
        btn.resize(btn.sizeHint())
        btn.pressed.connect(self.toggle_rec)
        vbox.addWidget(btn)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        
        # Set up a timer to update the plot
        timer = QTimer(self)
        timer.timeout.connect(self.update_line)
        timer.start(0.023)
    
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    #------------- UI callback methods--------------------------------       
    def toggle_rec(self):
        if self.playing:
            self.rec.stream_stop()
        else:
            self.rec.stream_start()
        self.playing = not self.playing
        
    def update_line(self):
        data = self.rec.get_buffer()
        data = data.reshape((len(data),))
        window = np.hanning(data.shape[0])
        fft_data = np.fft.rfft(window * data)
        psd_data = abs(fft_data)**2 / (np.abs(window)**2).sum()
        #print(len(psd_data))
        self.timeplotline.setData(y = data)
        #self.fftplotline.setData(abs(fft_data))
        self.fftplotline.setData(y = psd_data** 0.5)
        #self.canvas.draw()
        
    #----------------Overrding methods------------------------------------
    # The method to call when the mainWindow is being close       
    def closeEvent(self,event):
        reply = QMessageBox.question(self,'Message',
        'Are you sure you want to quit?', QMessageBox.Yes|
        QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.rec.close()
            event.accept()
        else:
            event.ignore()
            
#----------------Main loop------------------------------------         
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Example()
    sys.exit(app.exec_())
 
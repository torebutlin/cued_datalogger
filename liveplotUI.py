# -*- coding: utf-8 -*-
"""
Created on Wed Jul  5 13:12:34 2017

@author: eyt21
"""
from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QMainWindow,
    QPushButton, QDesktopWidget,QStatusBar)
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import pyqtSignal

import numpy as np

import pyqtgraph as pg
import myRecorder as rcd

from channel import Channel, ChannelSet

#--------------------- The LivePlotApp Class------------------------------------
class LiveplotApp(QMainWindow):
    
    dataSaved = pyqtSignal()
    
    def __init__(self,parent = None):
        super().__init__()
        self.parent = parent
        
        # Set window parameter
        self.setGeometry(500,500,500,500)
        self.setWindowTitle('LiveStreamPlot')
        
        # Set recorder object
        self.rec = rcd.Recorder(num_chunk = 6,
                                device_name = 'Line (U24XL with SPDIF I/O)')
        # Set playback to False to not hear anything
        self.rec.stream_init(playback = True)
        self.playing = True
        # Set up the TimeSeries and FreqSeries
        data = self.rec.get_buffer()
        self.timedata = np.arange(data.shape[0]) /self.rec.rate 
        self.freqdata = np.arange(int(data.shape[0]/2)+1) /data.shape[0] * self.rec.rate
        
        # Construct UI        
        self.initUI()
        
        # Center and show window
        self.center()
        self.setFocus()
        self.show()
        
     #---------------------- App construction methods-----------------------     
    def initUI(self):
        # Setup the plot canvas        
        self.main_widget = QWidget(self)
        vbox = QVBoxLayout(self.main_widget)
        
        # Set up time domain plot
        self.timeplotcanvas = pg.PlotWidget(self.main_widget, background = 'default')
        vbox.addWidget(self.timeplotcanvas)
        self.timeplot = self.timeplotcanvas.getPlotItem()
        self.timeplot.setLabels(title="Time Plot", bottom = 'Time(s)')
        self.timeplot.disableAutoRange(axis=None)
        self.timeplot.setRange(xRange = (0,self.timedata[-1]),yRange = (-2**7,2**7))
        self.timeplotline = self.timeplot.plot(pen='g')
        
        # Set up FFT plot
        self.fftplotcanvas = pg.PlotWidget(self.main_widget, background = 'default')
        vbox.addWidget(self.fftplotcanvas)
        self.fftplot = self.fftplotcanvas.getPlotItem()
        self.fftplot.setLabels(title="FFT Plot", bottom = 'Freq(Hz)')
        self.fftplot.disableAutoRange(axis=None)
        self.fftplot.setRange(xRange = (0,self.freqdata[-1]),yRange = (0, 2**8))
        self.fftplotline = self.fftplot.plot(pen = 'y')
        self.fftplotline.setDownsampling(auto = True) 
        
        self.update_line()
        
        # First set up the container to put the buttons in
        btn_container = QWidget(self.main_widget)
        # Set up the container to display horizontally
        hbox = QHBoxLayout(btn_container)
        # Put the buttons in
        self.togglebtn = QPushButton('Pause',btn_container)
        self.togglebtn.resize(self.togglebtn.sizeHint())
        self.togglebtn.pressed.connect(self.toggle_rec)
        hbox.addWidget(self.togglebtn)
        self.recordbtn = QPushButton('Record',btn_container)
        self.recordbtn.resize(self.recordbtn.sizeHint())
        self.recordbtn.pressed.connect(self.start_recording)
        hbox.addWidget(self.recordbtn)
        self.sshotbtn = QPushButton('Get Snapshot',btn_container)
        self.sshotbtn.resize(self.sshotbtn.sizeHint())
        self.sshotbtn.pressed.connect(self.get_snapshot)
        hbox.addWidget(self.sshotbtn)
        # Put the container into the main widget
        vbox.addWidget(btn_container)
        
        # Set up the status bar
        self.statusbar = QStatusBar(self.main_widget)
        self.statusbar.showMessage('Streaming')
        self.statusbar.messageChanged.connect(self.default_status)
        vbox.addWidget(self.statusbar)
        
        #Set the main widget as central widget
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        
        # Set up a timer to update the plot
        timer = QTimer(self)
        timer.timeout.connect(self.update_line)
        timer.start(25) # 25ms because that how roughly long the buffer fills up
   
    # Center the window
    def center(self):
        pr = self.parent.frameGeometry()
        qr = self.frameGeometry()
        print(qr.width())
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(pr.topLeft())
        self.move(qr.left() - qr.width(),qr.top())
    #------------- UI callback methods--------------------------------
    # Pause/Resume the stream       
    def toggle_rec(self):
        if self.playing:
            self.rec.stream_stop()
            self.togglebtn.setText('Resume')
            self.recordbtn.setDisabled(True)
        else:
            self.rec.stream_start()
            self.togglebtn.setText('Pause')
            self.recordbtn.setEnabled(True)
        self.playing = not self.playing
        # Clear the status, allow it to auto update itself
        self.statusbar.clearMessage()
    
    # Updates the plots    
    def update_line(self):
        data = self.rec.get_buffer()
        data = data.reshape((len(data),))
        window = np.hanning(data.shape[0])
        weightage = np.exp(-self.timedata / self.timedata[-1])[::-1]
        self.fft_data = np.fft.rfft(window * data * weightage)
        self.psd_data = abs(self.fft_data)**2 / (np.abs(window)**2).sum()
        self.timeplotline.setData(x = self.timedata, y = data)
        self.fftplotline.setData(x = self.freqdata, y = self.psd_data** 0.5)
    
    # Get the current instantaneous plot and transfer to main window     
    def get_snapshot(self):
        snapshot = self.rec.get_buffer()
        self.save_data(data = snapshot)
        self.statusbar.showMessage('Snapshot Captured!', 1500)
    
    # Start the data recording        
    def start_recording(self):
        self.statusbar.showMessage('Recording...')
        # Disable buttons
        for btn in self.main_widget.findChildren(QPushButton):
            btn.setDisabled(True)
        # Start the recording
        self.rec.recording = True
        # Setup the timer to stop the recording
        rec_timer = QTimer(self)
        rec_timer.setSingleShot(True)
        rec_timer.timeout.connect(self.stop_recording)
        rec_timer.start(3000)
    
    # Stop the data recording and transfer the recorded data to main window    
    def stop_recording(self):
        self.rec.recording = False
        for btn in self.main_widget.findChildren(QPushButton):
            btn.setEnabled(True)
        self.save_data(self.rec.flush_record_data())
        self.statusbar.clearMessage()
    
    # Transfer data to main window      
    def save_data(self,data = None):
        print('Saving data...')

        # Save the time series as a new channel
        self.parent.channel_set.new_channel(np.arange(data.size)/self.rec.rate, name="Time")
        # Save the data as a new channel
        self.parent.channel_set.new_channel(data, name="Value")
        
        self.dataSaved.emit()        
        print('Data saved!')
        

    
    # Set the status message to the default messages if it is empty       
    def default_status(self,*arg):
        if not arg[0]:
            if self.playing:
                self.statusbar.showMessage('Streaming')
            else:
                self.statusbar.showMessage('Stream Paused')
                
    #----------------Overrding methods------------------------------------
    # The method to call when the mainWindow is being close       
    def closeEvent(self,event):
        self.rec.close()
        event.accept()
        if self.parent:
            self.parent.liveplot = None
            self.parent.liveplotbtn.setText('Open Oscilloscope')
            
 
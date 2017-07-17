# -*- coding: utf-8 -*-
"""
Created on Wed Jul  5 13:12:34 2017

@author: eyt21
"""
import sys,traceback
from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QMainWindow,
    QPushButton, QDesktopWidget,QStatusBar, QLabel,QLineEdit, QFormLayout,
    QGroupBox,QRadioButton,QSplitter,QFrame, QComboBox,QScrollArea,QGridLayout,
    QCheckBox,QButtonGroup)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
#from PyQt5.QtGui import QImage
import numpy as np
import re

import pyqtgraph as pg

# Uncomment the NIRecorder later
import myRecorder as mR
import NIRecorder as NIR

from channel import DataSet, Channel, ChannelSet


PLAYBACK = False
#--------------------- The LivePlotApp Class------------------------------------
class LiveplotApp(QMainWindow):
    
    dataSaved = pyqtSignal()
    
    def __init__(self,parent = None):
        super().__init__()
        self.parent = parent
        
        # Set window parameter
        self.setGeometry(500,500,500,600)
        self.setWindowTitle('LiveStreamPlot')
        
        # Set recorder object
        self.rec = mR.Recorder(channels = 1,
                                num_chunk = 6,
                                device_name = 'Line (U24XL with SPDIF I/O)')
        # Set playback to False to not hear anything
        if self.rec.stream_init(playback = PLAYBACK):
            self.playing = True
            
        # Set up the TimeSeries and FreqSeries
        
        data = self.rec.get_buffer()
        self.timedata = np.arange(data.shape[0]) /self.rec.rate 
        self.freqdata = np.arange(int(data.shape[0]/2)+1) /data.shape[0] * self.rec.rate
        
        try:
            # Construct UI        
            self.initUI()
            self.config_setup()
        except Exception as e:
            print(e)
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))
            self.close()
            
            
             # Center and show window
            self.center()
            self.setFocus()
            self.show()
        
     #---------------------- App construction methods-----------------------     
    def initUI(self):
        # Set up the main widget        
        self.main_widget = QWidget(self)
        main_layout = QVBoxLayout(self.main_widget)
        
        #Set up the channel tickboxes widget
        self.channels_box = QWidget(self.main_widget)
        self.channels_layout = QGridLayout(self.channels_box)
        
        self.chan_btn_group = QButtonGroup(self.channels_box)
        self.chan_btn_group.setExclusive(False)
        for i in range (self.rec.channels):
            chan_btn = QCheckBox('Channel %i' % i,self.channels_box)
            chan_btn.setCheckState(Qt.Checked)
            self.channels_layout.addWidget(chan_btn)
            self.chan_btn_group.addButton(chan_btn,i)
            
        self.chan_btn_group.buttonClicked.connect(self.display_channel_plots)
        
        #print(self.channels_layout.count())
        
        scroll = QScrollArea(self.main_widget)
        #scroll.ensureVisible(50,50)
        scroll.setWidget(self.channels_box)
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll,10)
        
         # Set up the button layout to display horizontally
        btn_layout = QHBoxLayout(self.main_widget)
        # Put the buttons in
        self.togglebtn = QPushButton('Pause',self.main_widget)
        self.togglebtn.resize(self.togglebtn.sizeHint())
        self.togglebtn.pressed.connect(self.toggle_rec)
        btn_layout.addWidget(self.togglebtn)
        self.recordbtn = QPushButton('Record',self.main_widget)
        self.recordbtn.resize(self.recordbtn.sizeHint())
        self.recordbtn.pressed.connect(self.start_recording)
        btn_layout.addWidget(self.recordbtn)
        self.sshotbtn = QPushButton('Get Snapshot',self.main_widget)
        self.sshotbtn.resize(self.sshotbtn.sizeHint())
        self.sshotbtn.pressed.connect(self.get_snapshot)
        btn_layout.addWidget(self.sshotbtn)
        # Put the layout into the nongraphUI widget
        main_layout.addLayout(btn_layout)
        
        # Set up the splitter, add to main layout
        main_splitter = QSplitter(self.main_widget,orientation = Qt.Vertical)
        main_splitter.setOpaqueResize(opaque = False)
        main_layout.addWidget(main_splitter,90)
        
        self.plotlines = []
        # Set up time domain plot, add to splitter
        self.timeplotcanvas = pg.PlotWidget(main_splitter, background = 'default')
        main_splitter.addWidget(self.timeplotcanvas)
        self.timeplot = self.timeplotcanvas.getPlotItem()
        self.timeplot.setLabels(title="Time Plot", bottom = 'Time(s)')
        self.timeplot.disableAutoRange(axis=None)
        self.timeplot.setRange(xRange = (0,self.timedata[-1]),yRange = (-10,10))
       
        
        # Set up FFT plot, add to splitter
        self.fftplotcanvas = pg.PlotWidget(main_splitter, background = 'default')
        main_splitter.addWidget(self.fftplotcanvas)
        self.fftplot = self.fftplotcanvas.getPlotItem()
        self.fftplot.setLabels(title="FFT Plot", bottom = 'Freq(Hz)')
        self.fftplot.disableAutoRange(axis=None)
        self.fftplot.setRange(xRange = (0,self.freqdata[-1]),yRange = (0, 2**8))
        for i in range(self.rec.channels):
            #colour = pg.mkColor(125,23*i,255,120)
            self.plotlines.append(self.timeplot.plot(pen = 'g'))
            self.plotlines.append(self.fftplot.plot(pen = 'y'))
        
        self.update_line()

            
        # Set the rest of the UI and add to splitter
        nongraphUI = QWidget(main_splitter)
        nongraphUI_layout = QVBoxLayout(nongraphUI)
        
        
        # Set up the Acquisition layout to display horizontally
        config_layout = QHBoxLayout(nongraphUI)
        
        # Set the Acquisition settings form
        config_form = QFormLayout(nongraphUI)
        #config_form.setSpacing (2)
        
        # Set up the Acquisition type radiobuttons group
        self.typegroup = QGroupBox('Input Type', nongraphUI)
        typelbox = QHBoxLayout(self.typegroup)
        pyaudio_button = QRadioButton('SoundCard',self.typegroup)
        NI_button = QRadioButton('NI',self.typegroup)
        # Put the radiobuttons horizontally
        typelbox.addWidget(pyaudio_button)
        typelbox.addWidget(NI_button)
        
        # Set that to the layout of the group
        self.typegroup.setLayout(typelbox)
        
        # TODO: Give id to the buttons
        # Set up QbuttonGroup to manage the buttons' signals
        typebtngroup = QButtonGroup(self.typegroup)
        typebtngroup.addButton(pyaudio_button)
        typebtngroup.addButton(NI_button)
        typebtngroup.buttonReleased.connect(self.display_sources)
        # Add the group to Acquisition settings form
        config_form.addRow(self.typegroup)
        
        # Add the remaining settings to Acquisition settings form
        configs = ['Source','Rate','Channels','Chunk Size','Number of Chunks']
        self.configboxes = []
        
        for c in configs:
            if c is 'Source':
                cbox = QComboBox(nongraphUI)
                config_form.addRow(QLabel(c,nongraphUI),cbox)
                self.configboxes.append(cbox)
                
            else:
                cbox = QLineEdit(nongraphUI)
                config_form.addRow(QLabel(c,nongraphUI),cbox)
                self.configboxes.append(cbox)
            print(type(cbox),type(cbox) is QComboBox)    
            
        # Add the Acquisition form to the Acquisition layout
        config_layout.addLayout(config_form)
        
        # Add a button to Acquisition layout
        config_button = QPushButton('Set Config', nongraphUI)
        config_button.clicked.connect(self.ResetRecording)
        config_layout.addWidget(config_button)
        
        # Add Acquisition layout to nongraphUI widget
        nongraphUI_layout.addLayout(config_layout,10)
        
        # Set up the status bar and add to nongraphUI widget
        self.statusbar = QStatusBar(nongraphUI)
        self.statusbar.showMessage('Streaming')
        self.statusbar.messageChanged.connect(self.default_status)
        nongraphUI_layout.addWidget(self.statusbar)
        
        # Add nongraphUI widget to splitter
        main_splitter.addWidget(nongraphUI)
        main_splitter.setStretchFactor(0, 40)
        main_splitter.setStretchFactor(1, 40)
        main_splitter.setStretchFactor(2, 0)
        
        # Experimental styling
        main_splitter.setFrameShape(QFrame.Panel)
        main_splitter.setFrameShadow(QFrame.Sunken)
        self.main_widget.setStyleSheet('''
        .QWidget{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #eee, stop:1 #ccc);
            border: 1px solid #777;
            width: 13px;
            margin-top: 2px;
            margin-bottom: 2px;
            border-radius: 4px;
        }
        .QSplitter::handle:vertical{
                background: solid green;
        }                   ''')#background-image: url(Handle_bar.png);
        
        #Set the main widget as central widget
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        
        # Set up a timer to update the plot
        self.plottimer = QTimer(self)
        self.plottimer.timeout.connect(self.update_line)
        self.plottimer.start(self.rec.chunk_size*1000//self.rec.rate + 2) # 25ms because that how roughly long the buffer fills up
        
    def config_setup(self):
        rb = self.typegroup.findChildren(QRadioButton)
        if type(self.rec) is mR.Recorder:
            rb[0].setChecked(True)
        elif type(self.rec) is NIR.Recorder:
            rb[1].setChecked(True)
            
        self.display_sources()
        
        info = [ self.rec.rate,self.rec.channels,
                self.rec.chunk_size,self.rec.num_chunk]
        for cbox,i in zip(self.configboxes[1:],info):
            cbox.setText(str(i))
    
    def display_sources(self):
        # TODO: make use of the button input in callback
        rb = self.typegroup.findChildren(QRadioButton)
        if rb[0].isChecked():
            selR = mR.Recorder()
        elif rb[1].isChecked():
            selR = NIR.Recorder()
        else:
            return 0
        
        source_box = self.configboxes[0]
        source_box.clear()
        source_box.addItems(selR.available_devices()[0])
        if self.rec.device_name:
            source_box.setCurrentText(self.rec.device_name)
        
        del selR
         
    # Center the window
    def center(self):
        pr = self.parent.frameGeometry()
        qr = self.frameGeometry()
        print(qr.width())
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(pr.topLeft())
        self.move(qr.left() - qr.width(),qr.top())
    #---------------- Reset Methods-----------------------------------    
    def ResetRecording(self):
        self.statusbar.showMessage('Resetting...')
        
        # Stop the update and close the stream
        self.playing = False
        self.plottimer.stop()
        self.rec.close()
        print(type(self.rec))
        del self.rec
                
        try:    
            # Get Input from the Acquisition settings UI
            Rtype, settings = self.config_status()
            
            # Delete and reinitialise the recording object
            # Change the settings
            if Rtype[0]:
                self.rec = mR.Recorder(device_name = settings[0])
            elif Rtype[1]:
                self.rec = NIR.Recorder(device_name = settings[0])
            # TODO?: Change the values of recording object
            self.rec.rate = settings[1]
            self.rec.channels = settings[2]
            self.rec.chunk_size = settings[3]
            self.rec.num_chunk = settings[4]
        except Exception as e:
            print(e)
            print('Cannot set up new recorder')
        
        try:
        # Open the stream, plot and update
            self.rec.stream_init(playback = PLAYBACK)
            self.toggle_rec()
            self.ResetPlots()
            print(self.rec.chunk_size*1000//self.rec.rate + 1)
            self.plottimer.start(self.rec.chunk_size*1000//self.rec.rate + 1)
        except Exception as e:
            print(e)
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))
            print('Cannot stream,restart the app')
            
        try:
            self.ResetChanBtns()
        except Exception as e:
            print(e)
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))
            print('Cannot reset buttons')
            
        self.statusbar.clearMessage()
    
    def ResetXdata(self):
        data = self.rec.get_buffer()
        self.timedata = np.arange(data.shape[0]) /self.rec.rate 
        self.freqdata = np.arange(int(data.shape[0]/2)+1) /data.shape[0] * self.rec.rate
    
    def ResetPlots(self):
        print('resetting')
        try:
            n_plotlines = len(self.plotlines)
            self.ResetXdata()
            
            for _ in range(n_plotlines):
                line = self.plotlines.pop()
                line.clear()
                del line
                
            for _ in range(self.rec.channels):
                self.plotlines.append(self.timeplot.plot(pen = 'g'))
                self.plotlines.append(self.fftplot.plot(pen = 'y'))
            
            self.timeplot.setRange(xRange = (0,self.timedata[-1]),yRange = (-10,10))
            self.fftplot.setRange(xRange = (0,self.freqdata[-1]),yRange = (0, 2**8))
            self.update_line()
            
        except Exception as e:
            print(e)
            print('Cannot reset plots')
            
    def ResetChanBtns(self):
        for btn in self.chan_btn_group.buttons():
            btn.setCheckState(Qt.Checked)
            
        extra_btns = abs(self.rec.channels - self.channels_layout.count())
        if extra_btns:
            if self.rec.channels > self.channels_layout.count():
                for n in range(self.channels_layout.count(),self.rec.channels):
                    chan_btn = QCheckBox('Channel %i' % n,self.channels_box)
                    chan_btn.setCheckState(Qt.Checked)
                    self.channels_layout.addWidget(chan_btn)
                    self.chan_btn_group.addButton(chan_btn,n)
            else:
                for n in range(self.channels_layout.count()-1,self.rec.channels-1,-1):
                    chan_btn = self.chan_btn_group.button(n)
                    self.channels_layout.removeWidget(chan_btn)
                    self.chan_btn_group.removeButton(chan_btn)
                    chan_btn.deleteLater()
                pass
        
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
        window = np.hanning(data.shape[0])
        weightage = np.exp(-self.timedata / self.timedata[-1])[::-1]
        for i in range(data.shape[1]):
            plotdata = data[:,i].reshape((len(data[:,i]),)) + 50*i
            
            fft_data = np.fft.rfft(window * plotdata * weightage)
            psd_data = abs(fft_data)**2 / (np.abs(window)**2).sum() + 1e3 * i
            self.plotlines[2*i].setData(x = self.timedata, y = plotdata)
            self.plotlines[2*i+1].setData(x = self.freqdata, y = psd_data** 0.5)
    
    
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

        # Save the time series
        self.parent.cs.chans[0].set_data('t', np.arange(data.size)/self.rec.rate)
        # Save the values
        self.parent.cs.chans[0].set_data('y', data.reshape(data.size))
        
        self.dataSaved.emit()        
        print('Data saved!')
        
    
    # Set the status message to the default messages if it is empty       
    def default_status(self,*arg):
        if not arg[0]:
            if self.playing:
                self.statusbar.showMessage('Streaming')
            else:
                self.statusbar.showMessage('Stream Paused')
                
    def config_status(self, *arg):
        recType =  [rb.isChecked() for rb in self.typegroup.findChildren(QRadioButton)]
        configs = []
        for cbox in self.configboxes:
            if type(cbox) is QComboBox:
                configs.append(cbox.currentText())
            else:
                #notnumRegex = re.compile(r'(\D)+')
                config_input = cbox.text().strip(' ')
                configs.append(int(float(config_input)))
                    
        print(recType,configs)
        return(recType, configs)
    
    def display_channel_plots(self, *args):
        for btn in args:
            #print(btn)
            print(self.channels_box.findChildren(QCheckBox))
            print(self.chan_btn_group.id(btn))
            print(btn.isChecked())
            chan_num = self.chan_btn_group.id(btn)
            if btn.isChecked():
                self.plotlines[2*chan_num].setPen('g')
                self.plotlines[2*chan_num+1].setPen('y')
            else:
                self.plotlines[2*chan_num].setPen(None)
                self.plotlines[2*chan_num+1].setPen(None)
                
    #----------------Overrding methods------------------------------------
    # The method to call when the mainWindow is being close       
    def closeEvent(self,event):
        self.rec.close()
        event.accept()
        if self.parent:
            self.parent.liveplot = None
            self.parent.liveplotbtn.setText('Open Oscilloscope')
            
 

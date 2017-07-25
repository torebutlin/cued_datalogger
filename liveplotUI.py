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
from PyQt5.QtGui import QValidator,QIntValidator,QDoubleValidator
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
import pyqtgraph as pg
import numpy as np

import myRecorder as mR
try:
    import NIRecorder as NIR
    NI_drivers = True
except NotImplementedError:
    print("Seems like you don't have National Instruments drivers")
    NI_drivers = False
except ModuleNotFoundError:
    print("Seems like you don't have pyDAQmx modules")
    NI_drivers = False

# Theo's channel implementation, will probably use it later
from channel import DataSet, Channel, ChannelSet

# GLOBAL CONSTANTS
PLAYBACK = False
MAX_SAMPLE = 1e6
WIDTH = 900
HEIGHT = 500

#++++++++++++++++++++++++ The LivePlotApp Class +++++++++++++++++++++++++++
class LiveplotApp(QMainWindow):
#-------------------------- METADATA ----------------------------------  
    # Signal for when data has finished acquired
    dataSaved = pyqtSignal()
    
#---------------------- CONSTRUCTOR METHOD------------------------------    
    def __init__(self,parent = None):
        super().__init__()
        self.parent = parent
        
        # Set window parameter
        self.setGeometry(500,300,WIDTH,HEIGHT)
        self.setWindowTitle('LiveStreamPlot')
        
        # Set recorder object
        self.playing = False
        self.rec = mR.Recorder(channels = 15,
                                num_chunk = 6,
                                device_name = 'Line (U24XL with SPDIF I/O)')
        # Connect the recorder Signals
        self.connect_rec_signals()
        
        # Set up the TimeSeries and FreqSeries
        self.timedata = None 
        self.freqdata = None
        
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
            return
        
        # Attempt to start streaming
        self.init_and_check_stream()
            
        # Center and show window
        self.center()
        self.setFocus()
        self.show()

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++        
#++++++++++++++++++++++++ UI CONSTRUCTION START ++++++++++++++++++++++++++++++     
    def initUI(self):
        # Set up the main widget        
        self.main_widget = QWidget(self)
        main_layout = QHBoxLayout(self.main_widget)
        main_splitter = QSplitter(self.main_widget,orientation = Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
    #-------------------- ALL SPLITTER ------------------------------
        left_splitter = QSplitter(main_splitter,orientation = Qt.Vertical)
        mid_splitter = QSplitter(main_splitter,orientation = Qt.Vertical)
        right_splitter = QSplitter(main_splitter,orientation = Qt.Vertical)
        
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(mid_splitter)
        main_splitter.addWidget(right_splitter)
        
    #---------------------CHANNEL TOGGLE UI----------------------------------
        chanUI = QWidget(left_splitter)        
        # Set up the channel tickboxes widget
        chans_settings_layout = QVBoxLayout(chanUI)
        
        # Make the button tickboxes scrollable
        scroll = QScrollArea(left_splitter)
        
        self.channels_box = QWidget(scroll)
        self.checkbox_layout = QGridLayout(self.channels_box)
        
        # Set up the QbuttonGroup to manage the Signals
        self.chan_btn_group = QButtonGroup(self.channels_box)
        self.chan_btn_group.setExclusive(False)                
        self.ResetChanBtns()
        self.chan_btn_group.buttonClicked.connect(self.display_channel_plots)
        
        #scroll.ensureVisible(50,50)
        scroll.setWidget(self.channels_box)
        scroll.setWidgetResizable(True)
        
        chans_settings_layout.addWidget(scroll)
      
        # Set up the selection toggle buttons
        sel_btn_layout = QVBoxLayout()    
        sel_all_btn = QPushButton('Select All', left_splitter)
        sel_all_btn.clicked.connect(lambda: self.toggle_all_checkboxes(Qt.Checked))
        desel_all_btn = QPushButton('Deselect All',left_splitter)
        desel_all_btn.clicked.connect(lambda: self.toggle_all_checkboxes(Qt.Unchecked))
        inv_sel_btn = QPushButton('Invert Selection',left_splitter)
        inv_sel_btn.clicked.connect(self.invert_checkboxes)
        for y,btn in zip((0,1,2),(sel_all_btn,desel_all_btn,inv_sel_btn)):
            btn.resize(btn.sizeHint())
            sel_btn_layout.addWidget(btn)
            
        chans_settings_layout.addLayout(sel_btn_layout)
        #main_layout.addLayout(chans_settings_layout,10)
        left_splitter.addWidget(chanUI)
        
    #----------------DEVICE CONFIGURATION WIDGET---------------------------   
        configUI = QWidget(left_splitter)
        
        # Set the device settings form
        config_form = QFormLayout(configUI)
        config_form.setSpacing (2)
        
        # Set up the device type radiobuttons group
        self.typegroup = QGroupBox('Input Type', configUI)
        typelbox = QHBoxLayout(self.typegroup)
        pyaudio_button = QRadioButton('SoundCard',self.typegroup)
        NI_button = QRadioButton('NI',self.typegroup)
        typelbox.addWidget(pyaudio_button)
        typelbox.addWidget(NI_button)
        
        # Set that to the layout of the group
        self.typegroup.setLayout(typelbox)
        
        # TODO: Give id to the buttons
        # Set up QbuttonGroup to manage the buttons' Signals
        typebtngroup = QButtonGroup(self.typegroup)
        typebtngroup.addButton(pyaudio_button)
        typebtngroup.addButton(NI_button)
        typebtngroup.buttonReleased.connect(self.display_sources)
        
        config_form.addRow(self.typegroup)
        
        # Add the remaining settings to Acquisition settings form
        configs = ['Source','Rate','Channels','Chunk Size','Number of Chunks']
        self.configboxes = []
        
        for c in configs:
            if c is 'Source':
                cbox = QComboBox(configUI)
                config_form.addRow(QLabel(c,configUI),cbox)
                self.configboxes.append(cbox)
                
            else:
                cbox = QLineEdit(configUI)
                config_form.addRow(QLabel(c,configUI),cbox)
                self.configboxes.append(cbox)  
        
        # Add a button to device setting form
        self.config_button = QPushButton('Set Config', configUI)
        self.config_button.clicked.connect(self.ResetRecording)
        config_form.addRow(self.config_button)
        
        left_splitter.addWidget(configUI)
        
    #----------------------PLOT WIDGETS------------------------------------        
        self.plotlines = []
        # Set up time domain plot, add to splitter
        self.timeplotcanvas = pg.PlotWidget(mid_splitter, background = 'default')
        self.timeplot = self.timeplotcanvas.getPlotItem()
        self.timeplot.setLabels(title="Time Plot", bottom = 'Time(s)') 
        self.timeplot.disableAutoRange(axis=None)
        self.timeplot.setMouseEnabled(x=False,y = True)
        
        # Set up FFT plot, add to splitter
        self.fftplotcanvas = pg.PlotWidget(mid_splitter, background = 'default')
        self.fftplot = self.fftplotcanvas.getPlotItem()
        self.fftplot.setLabels(title="FFT Plot", bottom = 'Freq(Hz)')
        self.fftplot.disableAutoRange(axis=None)
        
        self.ResetPlots()
        mid_splitter.addWidget(self.timeplotcanvas)
        mid_splitter.addWidget(self.fftplotcanvas)
        
     #-------------------------STATUS BAR WIDGET--------------------------------
        # Set up the status bar
        self.statusbar = QStatusBar(mid_splitter)
        self.statusbar.showMessage('Streaming')
        self.statusbar.messageChanged.connect(self.default_status)
        self.statusbar.clearMessage()
        mid_splitter.addWidget(self.statusbar)    

    #---------------------------RECORDING WIDGET-------------------------------
        RecUI = QWidget(right_splitter)
        
        rec_settings_layout = QFormLayout(RecUI)
        
        # Add the recording setting UIs with the Validators
        configs = ['Samples','Seconds','Pretrigger','Ref. Channel','Trig. Level']
        default_values = ['','1.0', str(self.rec.pretrig_samples),
                          str(self.rec.trigger_channel),
                          str(self.rec.trigger_threshold)]
        validators = [QIntValidator(self.rec.chunk_size,MAX_SAMPLE),
                      QDoubleValidator(0.1,MAX_SAMPLE*self.rec.rate,1),
                      QIntValidator(-1,self.rec.chunk_size),
                      QIntValidator(0,self.rec.channels-1),
                      QDoubleValidator(0,5,2)]
        
        self.rec_boxes = []
        for c,v,vd in zip(configs,default_values,validators):
            cbox = QLineEdit(configUI)
            cbox.setText(v)
            cbox.setValidator(vd)
            rec_settings_layout.addRow(QLabel(c,configUI),cbox)
            self.rec_boxes.append(cbox)  
        
        # Connect the sample and time input check
        self.autoset_record_config('Time')
        self.rec_boxes[0].editingFinished.connect(lambda: self.autoset_record_config('Samples'))
        self.rec_boxes[1].editingFinished.connect(lambda: self.autoset_record_config('Time'))
        
        # Add the record and cancel buttons
        rec_buttons_layout = QHBoxLayout()
        
        self.recordbtn = QPushButton('Record',RecUI)
        self.recordbtn.resize(self.recordbtn.sizeHint())
        self.recordbtn.pressed.connect(self.start_recording)
        rec_buttons_layout.addWidget(self.recordbtn)
        self.cancelbtn = QPushButton('Cancel',RecUI)
        self.cancelbtn.resize(self.cancelbtn.sizeHint())
        self.cancelbtn.setDisabled(True)
        self.cancelbtn.pressed.connect(self.cancel_recording)
        rec_buttons_layout.addWidget(self.cancelbtn)
        
        rec_settings_layout.addRow(rec_buttons_layout)
        
        right_splitter.addWidget(RecUI)
        
    #---------------------PAUSE & SNAPSHOT BUTTONS-----------------------------
        freeze_btns = QWidget(right_splitter)
        # Set up the button layout to display horizontally
        btn_layout = QHBoxLayout(freeze_btns)
        # Put the buttons in
        self.togglebtn = QPushButton('Pause',right_splitter)
        self.togglebtn.resize(self.togglebtn.sizeHint())
        self.togglebtn.pressed.connect(lambda: self.toggle_rec())
        btn_layout.addWidget(self.togglebtn)
        self.sshotbtn = QPushButton('Get Snapshot',right_splitter)
        self.sshotbtn.resize(self.sshotbtn.sizeHint())
        self.sshotbtn.pressed.connect(self.get_snapshot)
        btn_layout.addWidget(self.sshotbtn)

        right_splitter.addWidget(freeze_btns)
        
    #------------------------FINALISE THE SPLITTERS-----------------------------
        #main_splitter.addWidget(acqUI)
        
        main_splitter.setSizes([WIDTH*0.1,WIDTH*0.8,WIDTH*0.1])        
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setStretchFactor(2, 0)
        
        
        #left_splitter.setSizes([HEIGHT*0.1,HEIGHT*0.8])
        mid_splitter.setSizes([HEIGHT*0.48,HEIGHT*0.48,HEIGHT*0.04])
        right_splitter.setSizes([HEIGHT*0.95,HEIGHT*0.05])
        
    #-----------------------EXPERIMENTAL STYLING---------------------------- 
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
        .QSplitter::handle{
                background: solid green;
        }                   ''')
        
    #-----------------------FINALISE THE MAIN WIDGET------------------------- 
        #Set the main widget as central widget
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        
        # Set up a timer to update the plot
        #self.plottimer = QTimer(self)
        #self.plottimer.timeout.connect(self.update_line)
        #self.plottimer.start(self.rec.chunk_size*1000//self.rec.rate + 2)
        
        self.show()
        
    #---------------------------UI ADJUSTMENTS----------------------------
        #h = 600 - chans_settings_layout.geometry().height()
        #main_splitter.setSizes([h*0.35,h*0.35,h*0.3])
        
#++++++++++++++++++++++++ UI CONSTRUCTION END +++++++++++++++++++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++        
#+++++++++++++++++++++ UI CALLBACK METHODS +++++++++++++++++++++++++++++++++++
    
#---------------------CHANNEL TOGGLE UI----------------------------------    
    def display_channel_plots(self, *args):
        for btn in args:
            chan_num = self.chan_btn_group.id(btn)
            if btn.isChecked():
                self.plotlines[2*chan_num].setPen('g')
                self.plotlines[2*chan_num+1].setPen('y')
            else:
                self.plotlines[2*chan_num].setPen(None)
                self.plotlines[2*chan_num+1].setPen(None)
                
    def invert_checkboxes(self):
        for btn in self.channels_box.findChildren(QCheckBox):
            btn.click()
         
    def toggle_all_checkboxes(self,state):
        for btn in self.channels_box.findChildren(QCheckBox):
            if not btn.checkState() == state:
                btn.click()
                
#---------------------PAUSE & SNAPSHOT BUTTONS-----------------------------
    # Pause/Resume the stream, unless explicitly specified to stop or not       
    def toggle_rec(self,stop = None):
        if not stop is None:
            self.playing = stop
            
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
   
    # Get the current instantaneous plot and transfer to main window     
    def get_snapshot(self):
        snapshot = self.rec.get_buffer()
        self.save_data(data = snapshot[:,0])
        self.statusbar.showMessage('Snapshot Captured!', 1500)
        
#----------------------PLOT WIDGETS-----------------------------------        
    # Updates the plots    
    def update_line(self):
        data = self.rec.get_buffer()
        window = np.hanning(data.shape[0])
        weightage = np.exp(2* self.timedata / self.timedata[-1])
        for i in range(data.shape[1]):
            plotdata = data[:,i].reshape((len(data[:,i]),)) + 1*i
            
            fft_data = np.fft.rfft(plotdata* window * weightage)
            psd_data = abs(fft_data)  + 1e2 * i
            self.plotlines[2*i].setData(x = self.timedata, y = plotdata)
            self.plotlines[2*i+1].setData(x = self.freqdata, y = psd_data** 0.5)
    
#----------------DEVICE CONFIGURATION WIDGET---------------------------    
    def config_setup(self):
        rb = self.typegroup.findChildren(QRadioButton)
        if type(self.rec) is mR.Recorder:
            rb[0].setChecked(True)
        elif type(self.rec) is NIR.Recorder:
            rb[1].setChecked(True)
            
        self.display_sources()
        
        info = [self.rec.rate,self.rec.channels,
                self.rec.chunk_size,self.rec.num_chunk]
        for cbox,i in zip(self.configboxes[1:],info):
            cbox.setText(str(i))
    
    def display_sources(self):
        # TODO: make use of the button input in callback?
        rb = self.typegroup.findChildren(QRadioButton)
        if not NI_drivers and rb[1].isChecked():
            print("You don't seem to have National Instrument drivers/modules")
            rb[0].setChecked(True)
            return 0
        
        if rb[0].isChecked():
            selR = mR.Recorder()
        elif rb[1].isChecked():
            selR = NIR.Recorder()
        else:
            return 0
        
        source_box = self.configboxes[0]
        source_box.clear()
        
        try:
            full_device_name = []
            s,b =  selR.available_devices()
            for a,b in zip(s,b):
                if type(b) is str:
                    full_device_name.append(a + ' - ' + b)
                else:
                    full_device_name.append(a)
                    
            source_box.addItems(full_device_name)
        except Exception as e:
            print(e)
            source_box.addItems(selR.available_devices()[0])
            
        if self.rec.device_name:
            source_box.setCurrentText(self.rec.device_name)
        del selR
                
    def read_device_config(self, *arg):
        recType =  [rb.isChecked() for rb in self.typegroup.findChildren(QRadioButton)]
        configs = []
        for cbox in self.configboxes:
            if type(cbox) is QComboBox:
                #configs.append(cbox.currentText())
                configs.append(cbox.currentIndex())
            else:
                #notnumRegex = re.compile(r'(\D)+')
                config_input = cbox.text().strip(' ')
                configs.append(int(float(config_input)))
                    
        print(recType,configs)
        return(recType, configs)
    
#---------------------------RECORDING WIDGET-------------------------------    
    # Start the data recording        
    def start_recording(self):
        rec_configs = self.read_record_config()
        
        if rec_configs[2]>=0:
            # Set up the trigger
            if self.rec.trigger_start(posttrig = rec_configs[0],
                                      duration = rec_configs[1],
                                      pretrig = rec_configs[2],
                                      channel = rec_configs[3],
                                      threshold = rec_configs[4]):
                self.statusbar.showMessage('Trigger Set!')
                for btn in self.main_widget.findChildren(QPushButton):
                    btn.setDisabled(True)
        else:
            self.rec.record_init(samples = rec_configs[0], duration = rec_configs[1])
            # Start the recording immediately
            if self.rec.record_start():
                self.statusbar.showMessage('Recording...')
                # Disable buttons
                for btn in [self.togglebtn, self.config_button, self.recordbtn]:
                    btn.setDisabled(True)
                
        self.cancelbtn.setEnabled(True)
    
    # Stop the data recording and transfer the recorded data to main window    
    def stop_recording(self):
        #self.rec.recording = False
        for btn in self.main_widget.findChildren(QPushButton):
            btn.setEnabled(True)
        self.cancelbtn.setDisabled(True)
        data = self.rec.flush_record_data()
        print(data[0,:])
        self.save_data(data[:,0])
        self.statusbar.clearMessage()
    
    # Cancel the data recording
    def cancel_recording(self):
        self.rec.record_cancel()
        for btn in self.main_widget.findChildren(QPushButton):
            btn.setEnabled(True)
        self.cancelbtn.setDisabled(True)
        self.statusbar.clearMessage()
        
    # Read the recording setting inputs
    def read_record_config(self, *arg):
        try:
            rec_configs = []
            data_type = [int,float,int,int,float]
            for cbox,dt in zip(self.rec_boxes,data_type):
                if type(cbox) is QComboBox:
                    #configs.append(cbox.currentText())
                    rec_configs.append(cbox.currentIndex())
                else:
                    config_input = cbox.text().strip(' ')
                    rec_configs.append(dt(float(config_input)))
            print(rec_configs)
            return(rec_configs)
        
        except Exception as e:
            print(e)
            return False
    
    # Auto set the time and samples based on recording limitations    
    def autoset_record_config(self, setting):
        sample_validator = self.rec_boxes[0].validator()
        time_validator = self.rec_boxes[1].validator()
        
        if setting == "Time":
            valid = time_validator.validate(self.rec_boxes[1].text(),0)[0]
            if not valid == QValidator.Acceptable:
                self.rec_boxes[1].setText(str(time_validator.bottom()))
                
            samples = int(float(self.rec_boxes[1].text())*self.rec.rate)
            valid = sample_validator.validate(str(samples),0)[0]
            if not valid == QValidator.Acceptable:
                samples = sample_validator.top()
        elif setting == 'Samples':
            samples = int(self.rec_boxes[0].text())        
        
        #samples = samples//self.rec.chunk_size  *self.rec.chunk_size
        duration = samples/self.rec.rate
        self.rec_boxes[0].setText(str(samples))
        self.rec_boxes[1].setText(str(duration))

#-------------------------STATUS BAR WIDGET--------------------------------
    # Set the status message to the default messages if it is empty (ie when cleared)       
    def default_status(self,*arg):
        if not arg[0]:
            if self.playing:
                self.statusbar.showMessage('Streaming')
            else:
                self.statusbar.showMessage('Stream Paused')
        
#+++++++++++++++++++++++++ UI CALLBACKS END++++++++++++++++++++++++++++++++++++   
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++   

#++++++++++++++++++++++++++ OTHER METHODS +++++++++++++++++++++++++++++++++++++        
#----------------------- APP ADJUSTMENTS METHODS-------------------------------               
    # Center the window
    def center(self):
        pr = self.parent.frameGeometry()
        qr = self.frameGeometry()
        print(qr.width())
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(pr.topLeft())
        self.move(qr.left() - qr.width(),qr.top())
        
#--------------------------- RESET METHODS-------------------------------------    
    def ResetRecording(self):
        self.statusbar.showMessage('Resetting...')
        
        # Stop the update and close the stream
        self.playing = False
        #self.plottimer.stop()
        self.rec.close()
        del self.rec
                
        try:    
            # Get Input from the Acquisition settings UI
            Rtype, settings = self.read_device_config()
            # Delete and reinitialise the recording object
            if Rtype[0]:
                self.rec = mR.Recorder()
            elif Rtype[1]:
                self.rec = NIR.Recorder()
            # Set the recorder parameters
            self.rec.set_device_by_name(self.rec.available_devices()[0][settings[0]])
            self.rec.rate = settings[1]
            self.rec.channels = settings[2]
            self.rec.chunk_size = settings[3]
            self.rec.num_chunk = settings[4]
        except Exception as e:
            print(e)
            print('Cannot set up new recorder')
        
        try:
            # Open the stream, plot and update
            self.init_and_check_stream()
            self.ResetPlots()
            print(self.rec.chunk_size*1000//self.rec.rate + 1)
            #self.plottimer.start(self.rec.chunk_size*1000//self.rec.rate + 1)
        except:
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))
            print('Cannot stream,restart the app')
        
        try:
            # Reset recording configuration Validators and inputs checks
            self.ResetRecConfigs()
            self.autoset_record_config('Samples')
        except:
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))
            print('Cannot recording configs')
        
        try:
            # Reset and change channel toggles
            self.ResetChanBtns()
        except:
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))
            print('Cannot reset buttons')
        
        self.connect_rec_signals()
        
    def ResetPlots(self):
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
            
            self.timeplot.setRange(xRange = (0,self.timedata[-1]),yRange = (-1,1))
            self.fftplot.setRange(xRange = (0,self.freqdata[-1]),yRange = (0, 2**4))
            self.fftplot.setLimits(xMin = 0,xMax = self.freqdata[-1],yMin = -20)
            self.update_line()
            
        except Exception as e:
            print(e)
            print('Cannot reset plots')
    
    def ResetXdata(self):
        data = self.rec.get_buffer()
        print(data.shape)
        self.timedata = np.arange(data.shape[0]) /self.rec.rate 
        self.freqdata = np.arange(int(data.shape[0]/2)+1) /data.shape[0] * self.rec.rate
        
    def ResetChanBtns(self):
        for btn in self.chan_btn_group.buttons():
            btn.setCheckState(Qt.Checked)
        
        n_buttons = self.checkbox_layout.count()
        extra_btns = abs(self.rec.channels - n_buttons)
        if extra_btns:
            if self.rec.channels > n_buttons:
                columns_limit = 4
                current_y = (n_buttons-1)//columns_limit
                current_x = (n_buttons-1)%columns_limit
                for n in range(n_buttons,self.rec.channels):
                    current_x +=1
                    if current_x%columns_limit == 0:
                        current_y +=1
                    current_x = current_x%columns_limit
                    
                    chan_btn = QCheckBox('Channel %i' % n,self.channels_box)
                    chan_btn.setCheckState(Qt.Checked)
                    self.checkbox_layout.addWidget(chan_btn,current_y,current_x)
                    self.chan_btn_group.addButton(chan_btn,n)
            else:
                for n in range(n_buttons-1,self.rec.channels-1,-1):
                    chan_btn = self.chan_btn_group.button(n)
                    self.checkbox_layout.removeWidget(chan_btn)
                    self.chan_btn_group.removeButton(chan_btn)
                    chan_btn.deleteLater()
                    
    def ResetRecConfigs(self):
           validators = [QIntValidator(self.rec.chunk_size,MAX_SAMPLE),
                         QDoubleValidator(0.1,MAX_SAMPLE*self.rec.rate,1),
                         QIntValidator(-1,self.rec.chunk_size),
                         QIntValidator(0,self.rec.channels-1)]
           
           for cbox,vd in zip(self.rec_boxes[:-1],validators):
                cbox.setValidator(vd)    
   
#----------------------- DATA TRANSFER METHODS -------------------------------    
    # Transfer data to main window      
    def save_data(self,data = None):
        print('Saving data...')

        # Save the time series
        self.parent.cs.chans[0].set_data('t', np.arange(data.size)/self.rec.rate)
        # Save the values
        self.parent.cs.chans[0].set_data('y', data.reshape(data.size))
        
        self.dataSaved.emit()        
        print('Data saved!')

#-------------------------- STREAM METHODS ------------------------------------        
    def init_and_check_stream(self):
         if self.rec.stream_init(playback = PLAYBACK):
            self.togglebtn.setEnabled(True)
            self.toggle_rec(stop = False)
            self.statusbar.showMessage('Streaming')
         else:
            self.togglebtn.setDisabled(True)
            self.toggle_rec(stop = True)
            self.statusbar.showMessage('Stream not initialised!')
            
    def connect_rec_signals(self):
            self.rec.rEmitter.recorddone.connect(self.stop_recording)
            self.rec.rEmitter.triggered.connect(self.trigger_message)
            self.rec.rEmitter.newdata.connect(self.update_line)
            
    def trigger_message(self):
        self.statusbar.showMessage('Triggered! Recording...')
        
#----------------------OVERRIDDEN METHODS------------------------------------
    # The method to call when the mainWindow is being close       
    def closeEvent(self,event):
        self.rec.close()
        event.accept()
        if self.parent:
            self.parent.liveplot = None
            self.parent.liveplotbtn.setText('Open Oscilloscope')
            
           
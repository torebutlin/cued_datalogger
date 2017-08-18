# -*- coding: utf-8 -*-
"""
Created on Wed Jul  5 13:12:34 2017

@author: eyt21
"""
import sys,traceback
from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QMainWindow,
    QPushButton, QDesktopWidget,QStatusBar, QLabel,QLineEdit, QFormLayout,
    QGroupBox,QRadioButton,QSplitter,QFrame, QComboBox,QScrollArea,QGridLayout,
    QCheckBox,QButtonGroup,QTextEdit,QApplication)
from PyQt5.QtGui import (QValidator,QIntValidator,QDoubleValidator,QColor,
QPalette,QPainter)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt5.Qt import QStyleOption,QStyle

import pyqtgraph as pg

import copy
import numpy as np
import functools as fct

from collections.abc import Sequence
from datalogger.acquisition.ChanLineText import ChanLineText
from datalogger.acquisition.ChanMetaWin import ChanMetaWin
#from acquisition.CustomPlot import CustomPlot
import datalogger.acquisition.myRecorder as mR
try:
    import datalogger.acquisition.NIRecorder as NIR
    NI_drivers = True
except NotImplementedError:
    print("Seems like you don't have National Instruments drivers")
    NI_drivers = False
except ImportError:
    print("ImportError: Seems like you don't have pyDAQmx modules")
    NI_drivers = False

from datalogger.api import channel as ch
from datalogger.api.custom_plot import CustomPlotWidget

import math

# GLOBAL CONSTANTS
PLAYBACK = False    # Whether to playback the stream
MAX_SAMPLE = 1e9    # Recording Sample max size limit
WIDTH = 900         # Window width
HEIGHT = 500        # Window height
CHANLVL_FACTOR = 0.1# The gap between each channel level (seems useless)
TRACE_DECAY = 0.005 # Increment size for decaying trace
TRACE_DURATION = 2  # Duration for a holding trace

#++++++++++++++++++++++++ The LivePlotApp Class +++++++++++++++++++++++++++
class LiveplotApp(QMainWindow):
#-------------------------- METADATA ----------------------------------  
    # Signal for when data has finished acquired
    dataSaved = pyqtSignal()
    done = pyqtSignal()
    
#---------------------- CONSTRUCTOR METHOD------------------------------    
    def __init__(self,parent = None):
        super().__init__()
        self.parent = parent
        
        # Set window parameter
        self.setGeometry(500,300,WIDTH,HEIGHT)
        self.setWindowTitle('LiveStreamPlot')
        self.center()
        
        self.meta_window = None
        
        
        # Set recorder object
        self.playing = False
        self.rec = mR.Recorder(channels = 2,
                                num_chunk = 6,
                                device_name = 'Line (U24XL with SPDIF I/O)')
        # Connect the recorder Signals
        self.connect_rec_signals()
        
        self.plottimer = QTimer(self)
        # Set up the TimeSeries and FreqSeries
        self.timedata = None 
        self.freqdata = None
        
        self.gen_plot_col()
        self.ResetMetaData()
           
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
            #self.close()
            self.show()
            return
        
        # Attempt to start streaming
        self.init_and_check_stream()
            
        # Center and show window
        
        self.setFocus()
        self.show()

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++        
#++++++++++++++++++++++++ UI CONSTRUCTION START ++++++++++++++++++++++++++++++     
    def initUI(self):
        # Set up the main widget        
        self.main_widget = QWidget(self)
        main_layout = QHBoxLayout(self.main_widget)
        self.main_splitter = QSplitter(self.main_widget,orientation = Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)
    #-------------------- ALL SPLITTER ------------------------------
        self.left_splitter = QSplitter(self.main_splitter,orientation = Qt.Vertical)
        self.mid_splitter = QSplitter(self.main_splitter,orientation = Qt.Vertical)
        self.right_splitter = QSplitter(self.main_splitter,orientation = Qt.Vertical)
        
        self.main_splitter.addWidget(self.left_splitter)
        self.main_splitter.addWidget(self.mid_splitter)
        self.main_splitter.addWidget(self.right_splitter)
        
    #---------------------CHANNEL TOGGLE UI----------------------------------
        #chantoggle_UI = QWidget(self.left_splitter)
        self.chantoggle_UI = ChanToggleUI(parent = self)
        
        self.ResetChanBtns()
        self.chantoggle_UI.chan_btn_group.buttonClicked.connect(self.display_channel_plots)
        self.chantoggle_UI.chan_text.returnPressed.connect(self.chan_line_toggle)
        self.chantoggle_UI.toggle_ext_button.clicked.connect(lambda: self.toggle_ext_toggling(True))

        self.left_splitter.addWidget(self.chantoggle_UI)
        
    #----------------CHANNEL CONFIGURATION WIDGET---------------------------
        self.chanconfig_UI = ChanConfigUI(self.left_splitter)
        
        self.chanconfig_UI.chans_num_box.currentIndexChanged.connect(self.display_chan_config)        
        self.chanconfig_UI.hold_tickbox.stateChanged.connect(self.signal_hold)
        self.chanconfig_UI.colbox.sigColorChanging.connect(lambda: self.set_plot_colour())
        self.chanconfig_UI.defcol_btn.clicked.connect(lambda: self.set_plot_colour(True))
        self.chanconfig_UI.meta_btn.clicked.connect(self.open_meta_window)
        
        for cbox,ax in zip(self.chanconfig_UI.time_offset_config,['x','y']):
            cbox.sigValueChanging.connect(fct.partial(self.set_plot_offset,ax,'Time'))
        for cbox,ax in zip(self.chanconfig_UI.fft_offset_config,['x','y']):
            cbox.sigValueChanging.connect(fct.partial(self.set_plot_offset,ax,'DFT'))
        
        self.ResetChanConfigs()
        
        self.left_splitter.addWidget(self.chanconfig_UI)
    #----------------DEVICE CONFIGURATION WIDGET---------------------------   
        self.devconfig_UI = DevConfigUI(self.left_splitter)
        
        self.devconfig_UI.typebtngroup.buttonReleased.connect(self.display_sources)
        self.devconfig_UI.config_button.clicked.connect(self.ResetRecording)
        
        self.left_splitter.addWidget(self.devconfig_UI)
        
    #----------------------PLOT WIDGETS------------------------------------        
        self.plotlines = []
        

        pg.setConfigOption('foreground', 'w')
        pg.setConfigOption('background', 'k')
        # Set up time domain plot, add to splitter
        self.timeplotcanvas = CustomPlotWidget(self.mid_splitter, background = 'default')
        self.timeplot = self.timeplotcanvas.getPlotItem()
        self.timeplot.setLabels(title="Time Plot", bottom = 'Time(s)') 
        #self.timeplot.disableAutoRange(axis=None)
        #self.timeplot.setMouseEnabled(x=True,y = True)
        
        # Set up FFT plot, add to splitter
        self.fftplotcanvas = pg.PlotWidget(self.mid_splitter, background = 'default')
        self.fftplot = self.fftplotcanvas.getPlotItem()
        self.fftplot.setLabels(title="FFT Plot", bottom = 'Freq(Hz)')
        self.fftplot.disableAutoRange(axis=None)
        
        self.ResetPlots()
        
        self.mid_splitter.addWidget(self.timeplotcanvas)
        self.mid_splitter.addWidget(self.fftplotcanvas)
        
    #-----------------------------STATUS WIDGET----------------------------
        self.stats_UI = StatusUI(self.mid_splitter)
        
        self.stats_UI.statusbar.messageChanged.connect(self.default_status)
        self.stats_UI.resetView.pressed.connect(self.ResetSplitterSizes)
        self.stats_UI.togglebtn.pressed.connect(lambda: self.toggle_rec())
        self.stats_UI.sshotbtn.pressed.connect(self.get_snapshot)

        self.mid_splitter.addWidget(self.stats_UI)
        
    #---------------------------RECORDING WIDGET-------------------------------
        self.RecUI = RecUI(self.right_splitter)
        
        # Connect the sample and time input check
        self.RecUI.rec_boxes[0].editingFinished.connect(lambda: self.autoset_record_config('Samples'))
        self.RecUI.rec_boxes[1].editingFinished.connect(lambda: self.autoset_record_config('Time'))
        self.RecUI.rec_boxes[2].editingFinished.connect(lambda: self.set_input_limits(self.RecUI.rec_boxes[2],-1,self.rec.chunk_size,int))
        self.RecUI.rec_boxes[2].textEdited.connect(self.toggle_trigger)
        self.RecUI.rec_boxes[4].textEdited.connect(self.change_threshold)

        self.RecUI.recordbtn.pressed.connect(self.start_recording)
        self.RecUI.cancelbtn.pressed.connect(self.cancel_recording)
       
        self.ResetRecConfigs()
        self.autoset_record_config('Time')
        self.right_splitter.addWidget(self.RecUI)
        
    #-----------------------CHANNEL LEVELS WIDGET------------------------------
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
        
        self.ResetChanLvls()
        self.right_splitter.addWidget(chanlevel_UI)
    
    #------------------------FINALISE THE SPLITTERS-----------------------------
        #self.main_splitter.addWidget(acqUI)
   
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStretchFactor(2, 0)
        
        self.main_splitter.setCollapsible (1, False)
        self.mid_splitter.setCollapsible (2, False)
        self.ResetSplitterSizes()
        
    #-----------------------EXPERIMENTAL STYLING---------------------------- 
        self.main_splitter.setFrameShape(QFrame.Panel)
        self.main_splitter.setFrameShadow(QFrame.Sunken)
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
                background: #737373;
        }
        .QGroupBox{
                border: 1px solid black;
                margin-top: 0.5em;
                font: italic;
        }
        .QGroupBox::title {
                top: -6px;
                left: 10px;
        }
        .QWidget #subWidget{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eee, stop:1 #ccc);
                border: 1px solid #777;
                width: 13px;
                margin-top: 2px;
                margin-bottom: 2px;
                border-radius: 4px;
            }                   
        ''') 
        

        
    
    #-----------------------FINALISE THE MAIN WIDGET------------------------- 
        #Set the main widget as central widget
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        
        # Set up a timer to update the plot
        self.plottimer.timeout.connect(self.update_line)
        #self.plottimer.timeout.connect(self.update_chanlvls)
        self.plottimer.start(self.rec.chunk_size*1000//self.rec.rate)
        
        self.show()
        
        #h = 600 - chans_settings_layout.geometry().height()
        #self.main_splitter.setSizes([h*0.35,h*0.35,h*0.3])
        
    #---------------------------ADDITIONAL UIs----------------------------
        self.chan_toggle_ext = AdvToggleUI(self.main_widget)
        self.chan_toggle_ext.chan_text2.returnPressed.connect(self.chan_line_toggle)
        self.chan_toggle_ext.close_ext_toggle.clicked.connect(lambda: self.toggle_ext_toggling(False))
     
#++++++++++++++++++++++++ UI CONSTRUCTION END +++++++++++++++++++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++        
#+++++++++++++++++++++ UI CALLBACK METHODS +++++++++++++++++++++++++++++++++++
    
#---------------------CHANNEL TOGGLE UI----------------------------------    
    def display_channel_plots(self, btn):
        chan_num = self.chantoggle_UI.chan_btn_group.id(btn)
        if btn.isChecked():
            self.plotlines[2*chan_num].setPen(self.plot_colours[chan_num])
            self.plotlines[2*chan_num+1].setPen(self.plot_colours[chan_num])
        else:
            self.plotlines[2*chan_num].setPen(None)
            self.plotlines[2*chan_num+1].setPen(None)
   
    def toggle_ext_toggling(self,toggle):
        if toggle:
            tlpoint = self.chantoggle_UI.chan_text.mapTo(self,QPoint(0,0))
            self.chan_toggle_ext.resize(self.chan_toggle_ext.sizeHint())
            self.chan_toggle_ext.setGeometry(tlpoint.x(),tlpoint.y(),
                                             self.chantoggle_UI.chan_text.width()*3,
                                             self.chantoggle_UI.chan_text.height()*15)
            if not self.chan_toggle_ext.isVisible():
                self.chan_toggle_ext.show()
        else:
            self.chan_toggle_ext.hide()
     
    def chan_line_toggle(self,chan_list):
        '''
        try:
            expression = eval(string)
        except:
            t,v,_ = sys.exc_info()
            print(t)
            print(v)
            print('Invalid expression')
            return False
        '''
        all_selected_chan = []
        for str_in in chan_list:
            r_in = str_in.split(':')
            if len(r_in) == 1:
                if r_in[0]:
                    all_selected_chan.append(int(r_in[0]))
            elif len(r_in) >1: 
                if not r_in[0]:
                    r_in[0] = 0
                if not r_in[1]:
                    r_in[1] = self.rec.channels
                    
                if len(r_in) == 2:
                    all_selected_chan.extend(range(int(r_in[0]),int(r_in[1])))
                else:
                    if not r_in[2]:
                        r_in[2] = 1
                    all_selected_chan.extend(range(int(r_in[0]),int(r_in[1]),int(r_in[2])))
                    
                    
        '''
        if isinstance(expression,Sequence) and not isinstance(expression,str) :
            for n in expression:
                if isinstance(n,Sequence) and not isinstance(n,str):
                    all_selected_chan.extend(n)
                elif isinstance(expression,int):
                    all_selected_chan.append(n)
        elif isinstance(expression,int):
            all_selected_chan.append(expression)
        '''    
        print(all_selected_chan)
        
        if all_selected_chan:
            self.toggle_all_checkboxes(Qt.Unchecked)
            for chan in set(all_selected_chan):
                if chan < self.rec.channels:
                    self.chantoggle_UI.chan_btn_group.button(chan).click()
         
#----------------CHANNEL CONFIGURATION WIDGET---------------------------    
    def display_chan_config(self, arg):
        if type(arg) == pg.PlotDataItem:
            num = self.plotlines.index(arg) // 2
            self.chanconfig_UI.chans_num_box.setCurrentIndex(num)
        else:
            num = arg
        
        self.chanconfig_UI.colbox.setColor(self.plot_colours[num])
        self.chanconfig_UI.time_offset_config[0].setValue(self.plot_xoffset[0,num])
        self.chanconfig_UI.time_offset_config[1].setValue(self.plot_yoffset[0,num])
        self.chanconfig_UI.fft_offset_config[0].setValue(self.plot_xoffset[1,num])
        self.chanconfig_UI.fft_offset_config[1].setValue(self.plot_yoffset[1,num])
        self.chanconfig_UI.hold_tickbox.setCheckState(self.sig_hold[num])
        
    def set_plot_offset(self, offset,set_type, sp,num):
        chan = self.chanconfig_UI.chans_num_box.currentIndex()
        if set_type == 'Time':
            data_type = 0
        elif set_type == 'DFT':
            data_type = 1
            
        if offset == 'x':
            self.plot_xoffset[data_type,chan] = num
        elif offset == 'y':
            self.plot_yoffset[data_type,chan] = num
            
    def set_offset_step(self,cbox,num):
        cbox.setSingleStep(num)
        
    def signal_hold(self,state):
        chan = self.chanconfig_UI.chans_num_box.currentIndex()
        self.sig_hold[chan] = state
    
    def set_plot_colour(self,reset = False):
        chan = self.chanconfig_UI.chans_num_box.currentIndex()
        chan_btn = self.chantoggle_UI.chan_btn_group.button(chan)
            
        if reset:
            col = self.def_colours[chan]
            self.chanconfig_UI.colbox.setColor(col)
        else:
            col = self.chanconfig_UI.colbox.color()
        
        self.plot_colours[chan] = col;
        if chan_btn.isChecked():
            self.plotlines[2*chan].setPen(col)
            self.plotlines[2*chan+1].setPen(col)
        self.chanlvl_pts.scatter.setBrush(self.plot_colours)
    
    def open_meta_window(self):
        if not self.meta_window:
            try:
                self.meta_window = ChanMetaWin(self)
                self.meta_window.show()
                self.meta_window.finished.connect(self.meta_win_closed)
            except:
                t,v,tb = sys.exc_info()
                print(t)
                print(v)
                print(traceback.format_tb(tb))
                
    def meta_win_closed(self):
        self.meta_window = None
        self.update_chan_names()

#---------------------PAUSE & SNAPSHOT BUTTONS-----------------------------
    # Pause/Resume the stream, unless explicitly specified to stop or not       
    def toggle_rec(self,stop = None):
        if not stop == None:
            self.playing = stop
            
        if self.playing:
            self.rec.stream_stop()
            self.stats_UI.togglebtn.setText('Resume')
            self.RecUI.recordbtn.setDisabled(True)
        else:
            self.rec.stream_start()
            self.stats_UI.togglebtn.setText('Pause')
            self.RecUI.recordbtn.setEnabled(True)
        self.playing = not self.playing
        # Clear the status, allow it to auto update itself
        self.stats_UI.statusbar.clearMessage()
        
    # Get the current instantaneous plot and transfer to main window     
    def get_snapshot(self):
        snapshot = self.rec.get_buffer()
        self.save_data(data = snapshot[:,0])
        self.stats_UI.statusbar.showMessage('Snapshot Captured!', 1500)
        
#----------------------PLOT WIDGETS-----------------------------------              
    # Updates the plots    
    def update_line(self):
        # TODO: can this be merge with update channel levels plot
        data = self.rec.get_buffer()
        window = np.hanning(data.shape[0])
        weightage = np.exp(2* self.timedata / self.timedata[-1])
        currentdata = data[len(data)-self.rec.chunk_size:,:]
        currentdata -= np.mean(currentdata)
        rms = np.sqrt(np.mean(currentdata ** 2,axis = 0))
        maxs = np.amax(abs(currentdata),axis = 0)
        
        self.chanlvl_bars.setData(x = rms,y = np.arange(self.rec.channels)*CHANLVL_FACTOR, right = maxs-rms,left = rms)
        self.chanlvl_pts.setData(x = rms,y = np.arange(self.rec.channels)*CHANLVL_FACTOR)

        for i in range(data.shape[1]):
            plotdata = data[:,i].reshape((len(data[:,i]),))
            zc = 0
            if self.sig_hold[i] == Qt.Checked:
                avg = np.mean(plotdata);
                zero_crossings = np.where(np.diff(np.sign(plotdata-avg))>0)[0]
                if zero_crossings.shape[0]:
                    zc = zero_crossings[0]+1
                
            self.plotlines[2*i].setData(x = self.timedata[:len(plotdata)-zc] + 
            self.plot_xoffset[0,i], y = plotdata[zc:] + self.plot_yoffset[0,i])

            fft_data = np.fft.rfft(plotdata* window * weightage)
            psd_data = abs(fft_data)** 0.5
            self.plotlines[2*i+1].setData(x = self.freqdata + self.plot_xoffset[1,i], y = psd_data  + self.plot_yoffset[1,i])

            if self.trace_counter[i]>self.trace_countlimit:
                self.peak_trace[i] = max(self.peak_trace[i]*math.exp(-self.peak_decays[i]),0)
                self.peak_decays[i] += TRACE_DECAY
            self.trace_counter[i] += 1
            
            if self.peak_trace[i]<maxs[i]:
                self.peak_trace[i] = maxs[i]
                self.peak_decays[i] = 0
                self.trace_counter[i] = 0
                
            self.peak_plots[i].setData(x = [self.peak_trace[i],self.peak_trace[i]],
                           y = [(i-0.3)*CHANLVL_FACTOR, (i+0.3)*CHANLVL_FACTOR])
            
            self.peak_plots[i].setPen(self.level_colourmap.map(self.peak_trace[i]))

#----------------DEVICE CONFIGURATION WIDGET---------------------------    
    def config_setup(self):
        rb = self.devconfig_UI.typegroup.findChildren(QRadioButton)
        if type(self.rec) == mR.Recorder:
            rb[0].setChecked(True)
        elif type(self.rec) == NIR.Recorder:
            rb[1].setChecked(True)
            
        self.display_sources()
        
        info = [self.rec.rate,self.rec.channels,
                self.rec.chunk_size,self.rec.num_chunk]
        for cbox,i in zip(self.devconfig_UI.configboxes[1:],info):
            cbox.setText(str(i))
    
    def display_sources(self):
        # TODO: make use of the button input in callback?
        rb = self.devconfig_UI.typegroup.findChildren(QRadioButton)
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
        
        source_box = self.devconfig_UI.configboxes[0]
        source_box.clear()
        
        try:
            full_device_name = []
            s,b =  selR.available_devices()
            for a,b in zip(s,b):
                if type(b) == str:
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
        recType =  [rb.isChecked() for rb in self.devconfig_UI.typegroup.findChildren(QRadioButton)]
        configs = []
        for cbox in self.devconfig_UI.configboxes:
            if type(cbox) == QComboBox:
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
        print(type(self.rec))
        if rec_configs[2]>=0:
            # Set up the trigger
            if self.rec.trigger_start(posttrig = rec_configs[0],
                                      duration = rec_configs[1],
                                      pretrig = rec_configs[2],
                                      channel = rec_configs[3],
                                      threshold = rec_configs[4]):
                self.stats_UI.statusbar.showMessage('Trigger Set!')
                for btn in self.main_widget.findChildren(QPushButton):
                    btn.setDisabled(True)
        else:
            self.rec.record_init(samples = rec_configs[0], duration = rec_configs[1])
            # Start the recording immediately
            if self.rec.record_start():
                self.stats_UI.statusbar.showMessage('Recording...')
                # Disable buttons
                for btn in [self.stats_UI.togglebtn, self.devconfig_UI.config_button, self.RecUI.recordbtn]:
                    btn.setDisabled(True)
                
        self.RecUI.cancelbtn.setEnabled(True)
    
    # Stop the data recording and transfer the recorded data to main window    
    def stop_recording(self):
        #self.rec.recording = False
        for btn in self.main_widget.findChildren(QPushButton):
            btn.setEnabled(True)
        self.RecUI.cancelbtn.setDisabled(True)
        data = self.rec.flush_record_data()
        self.save_data(data)
        self.stats_UI.statusbar.clearMessage()
    
    # Cancel the data recording
    def cancel_recording(self):
        self.rec.record_cancel()
        for btn in self.main_widget.findChildren(QPushButton):
            btn.setEnabled(True)
        self.RecUI.cancelbtn.setDisabled(True)
        self.stats_UI.statusbar.clearMessage()
        
    # Read the recording setting inputs
    def read_record_config(self, *arg):
        try:
            rec_configs = []
            data_type = [int,float,int,int,float]
            for cbox,dt in zip(self.RecUI.rec_boxes,data_type):
                if type(cbox) == QComboBox:
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
        sample_validator = self.RecUI.rec_boxes[0].validator()
        time_validator = self.RecUI.rec_boxes[1].validator()
        
        if setting == "Time":
            valid = time_validator.validate(self.RecUI.rec_boxes[1].text(),0)[0]
            if not valid == QValidator.Acceptable:
                self.RecUI.rec_boxes[1].setText(str(time_validator.bottom()))
                
            samples = int(float(self.RecUI.rec_boxes[1].text())*self.rec.rate)
            valid = sample_validator.validate(str(samples),0)[0]
            if not valid == QValidator.Acceptable:
                samples = sample_validator.top()
        elif setting == 'Samples':
            samples = int(self.RecUI.rec_boxes[0].text())        
        
        #samples = samples//self.rec.chunk_size  *self.rec.chunk_size
        duration = samples/self.rec.rate
        self.RecUI.rec_boxes[0].setText(str(samples))
        self.RecUI.rec_boxes[1].setText(str(duration))

#-------------------------CHANNEL LEVELS WIDGET--------------------------------       
    def change_threshold(self,arg):
        if type(arg) == str:
            self.threshold_line.setValue(float(arg))
        else:
            self.RecUI.rec_boxes[4].setText('%.2f' % arg.value())
        
#-------------------------STATUS BAR WIDGET--------------------------------
    # Set the status message to the default messages if it is empty (ie when cleared)       
    def default_status(self,*arg):
        if not arg[0]:
            if self.playing:
                self.stats_UI.statusbar.showMessage('Streaming')
            else:
                self.stats_UI.statusbar.showMessage('Stream Paused')
        
#+++++++++++++++++++++++++ UI CALLBACKS END++++++++++++++++++++++++++++++++++++   
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++   

#++++++++++++++++++++++++++ OTHER METHODS +++++++++++++++++++++++++++++++++++++        
#----------------------- APP ADJUSTMENTS METHODS-------------------------------               
    # Center the window
    def center(self):
        if self.parent:
            pr = self.parent.frameGeometry()
            qr = self.frameGeometry()
            print(qr.width())
            cp = QDesktopWidget().availableGeometry().center()
            qr.moveCenter(cp)
            self.move(pr.topLeft())
            self.move(qr.left() - qr.width(),qr.top())
        
#--------------------------- RESET METHODS-------------------------------------    
    def ResetRecording(self):
        self.stats_UI.statusbar.showMessage('Resetting...')
        
        # Stop the update and close the stream
        self.playing = False
        self.plottimer.stop()
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
            dev_name = self.rec.available_devices()[0]
            sel_ind = min(settings[0],len(dev_name)-1)
            self.rec.set_device_by_name(dev_name[sel_ind])
            self.rec.rate = settings[1]
            self.rec.channels = settings[2]
            self.rec.chunk_size = settings[3]
            self.rec.num_chunk = settings[4]
            self.devconfig_UI.configboxes[0].setCurrentIndex(dev_name.index(self.rec.device_name))
        except Exception as e:
            print(e)
            print('Cannot set up new recorder')
            
        
        try:
            # Open the stream, plot and update
            self.init_and_check_stream()
            # Reset channel configs
            self.ResetChanConfigs()
            self.ResetPlots()
            self.ResetChanLvls()
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

        # Reset and change channel toggles
        self.ResetMetaData()
        self.ResetChanBtns()
        self.connect_rec_signals()
        
        self.plottimer.start(self.rec.chunk_size*1000//self.rec.rate)
        
    def ResetPlots(self):
        n_plotlines = len(self.plotlines)
        self.ResetXdata()
        
        for _ in range(n_plotlines):
            line = self.plotlines.pop()
            line.clear()
            del line
            
        for i in range(self.rec.channels):
            tplot = self.timeplot.plot(pen = self.plot_colours[i])
            tplot.curve.setClickable(True,width = 4)
            tplot.sigClicked.connect(self.display_chan_config)
            self.plotlines.append(tplot)
            
            fplot = self.fftplot.plot(pen = self.plot_colours[i])
            fplot.curve.setClickable(True,width = 4)
            fplot.sigClicked.connect(self.display_chan_config)
            self.plotlines.append(fplot)
        
        self.fftplot.setRange(xRange = (0,self.freqdata[-1]),yRange = (0, 100*self.rec.channels))
        self.fftplot.setLimits(xMin = 0,xMax = self.freqdata[-1],yMin = -20)
    
    def ResetXdata(self):
        data = self.rec.get_buffer()
        self.timedata = np.arange(data.shape[0]) /self.rec.rate 
        self.freqdata = np.arange(int(data.shape[0]/2)+1) /data.shape[0] * self.rec.rate
        
    def ResetChanLvls(self): 
        self.chanlvl_pts.clear()
        self.chanlvl_pts = self.channelvlplot.plot(pen = None,symbol='o',
                                                  symbolBrush = self.plot_colours,
                                                  symbolPen = None)
        
        for _ in range(len(self.peak_plots)):
            line = self.peak_plots.pop()
            line.clear()
            del line
        
        self.peak_trace = np.zeros(self.rec.channels)
        self.peak_decays = np.zeros(self.rec.channels)
        self.trace_counter = np.zeros(self.rec.channels)
        self.trace_countlimit = TRACE_DURATION *self.rec.rate//self.rec.chunk_size  
        
        self.threshold_line.setBounds((0,self.rec.max_value))
        
        for i in range(self.rec.channels):
            self.peak_plots.append(self.channelvlplot.plot(x = [self.peak_trace[i],self.peak_trace[i]],
                                                          y = [(i-0.3*CHANLVL_FACTOR), (i+0.3)*CHANLVL_FACTOR])) 
        
        self.channelvlplot.setRange(xRange = (0,self.rec.max_value+0.1),yRange = (-0.5*CHANLVL_FACTOR, (self.rec.channels+5-0.5)*CHANLVL_FACTOR))
        self.channelvlplot.setLimits(xMin = -0.1,xMax = self.rec.max_value+0.1,yMin = -0.5*CHANLVL_FACTOR,yMax = (self.rec.channels+5-0.5)*CHANLVL_FACTOR)
        
    def ResetChanBtns(self):
        for btn in self.chantoggle_UI.chan_btn_group.buttons():
            btn.setCheckState(Qt.Checked)
        
        n_buttons = self.chantoggle_UI.checkbox_layout.count()
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
                    
                    chan_btn = QCheckBox('Channel %i' % n,self.chantoggle_UI.channels_box)
                    chan_btn.setCheckState(Qt.Checked)
                    self.chantoggle_UI.checkbox_layout.addWidget(chan_btn,current_y,current_x)
                    self.chantoggle_UI.chan_btn_group.addButton(chan_btn,n)
            else:
                for n in range(n_buttons-1,self.rec.channels-1,-1):
                    chan_btn = self.chantoggle_UI.chan_btn_group.button(n)
                    self.chantoggle_UI.checkbox_layout.removeWidget(chan_btn)
                    self.chantoggle_UI.chan_btn_group.removeButton(chan_btn)
                    chan_btn.deleteLater()
            
        self.update_chan_names()
                    
    def ResetRecConfigs(self):
        self.RecUI.rec_boxes[3].clear()
        self.RecUI.rec_boxes[3].addItems([str(i) for i in range(self.rec.channels)])
    
        validators = [QDoubleValidator(0.1,MAX_SAMPLE*self.rec.rate,1),
                     QIntValidator(-1,self.rec.chunk_size)]
        for cbox,vd in zip(self.RecUI.rec_boxes[1:-2],validators):
            cbox.setValidator(vd)    
                
    def ResetChanConfigs(self):
        self.plot_xoffset = np.zeros(shape = (2,self.rec.channels))
        self.plot_yoffset = np.repeat(np.arange(float(self.rec.channels)).reshape(1,self.rec.channels),2,axis = 0) * [[1],[50]]
        self.sig_hold = [Qt.Unchecked]* self.rec.channels
        c_list = self.plot_colourmap.getLookupTable(nPts = self.rec.channels)
        self.plot_colours = []
        self.def_colours = []
        for i in range(self.rec.channels):
            r,g,b = c_list[i]
            self.plot_colours.append(QColor(r,g,b))
            self.def_colours.append(QColor(r,g,b))

        self.chanconfig_UI.chans_num_box.clear()
        self.chanconfig_UI.chans_num_box.addItems([str(i) for i in range(self.rec.channels)])
        self.chanconfig_UI.chans_num_box.setCurrentIndex(0)
        
        self.display_chan_config(0)
    
    def ResetMetaData(self):
        self.live_chanset = ch.ChannelSet(self.rec.channels)
        self.live_chanset.add_channel_dataset(tuple(range(self.rec.channels)), 'time_series')
        
        
    def ResetSplitterSizes(self):
        #self.left_splitter.setSizes([HEIGHT*0.1,HEIGHT*0.8])
        self.main_splitter.setSizes([WIDTH*0.25,WIDTH*0.55,WIDTH*0.2]) 
        self.mid_splitter.setSizes([HEIGHT*0.48,HEIGHT*0.48,HEIGHT*0.04])
        self.right_splitter.setSizes([HEIGHT*0.05,HEIGHT*0.85])
        
    def update_chan_names(self):
        names = self.live_chanset.get_channel_metadata(tuple(range(self.rec.channels)),'name')
        for n,name in enumerate(names):
            chan_btn = self.chantoggle_UI.chan_btn_group.button(n)
            chan_btn.setText(name)
        
#----------------------- DATA TRANSFER METHODS -------------------------------    
    # Transfer data to main window      
    def save_data(self,data = None):
        print('Saving data...')
        for i in range(data.shape[1]):
            self.live_chanset.set_channel_data(i,'time_series',data[:,i])
        self.live_chanset.set_channel_metadata(tuple(range(data.shape[1]))
                                                ,{'sample_rate':self.rec.rate})
        self.parent.cs = copy.copy(self.live_chanset)
        self.dataSaved.emit()        
        print('Data saved!')

#-------------------------- STREAM METHODS ------------------------------------        
    def init_and_check_stream(self):
         if self.rec.stream_init(playback = PLAYBACK):
            self.stats_UI.togglebtn.setEnabled(True)
            self.toggle_rec(stop = False)
            self.stats_UI.statusbar.showMessage('Streaming')
         else:
            self.stats_UI.togglebtn.setDisabled(True)
            self.toggle_rec(stop = True)
            self.stats_UI.statusbar.showMessage('Stream not initialised!')
            
    def connect_rec_signals(self):
            self.rec.rEmitter.recorddone.connect(self.stop_recording)
            self.rec.rEmitter.triggered.connect(self.trigger_message)
            #self.rec.rEmitter.newdata.connect(self.update_line)
            #self.rec.rEmitter.newdata.connect(self.update_chanlvls)
            
    def trigger_message(self):
        self.stats_UI.statusbar.showMessage('Triggered! Recording...')
 #-------------------------- COLOUR METHODS ------------------------------------       
    def gen_plot_col(self):
        val = [0.0,0.5,1.0]
        colour = np.array([[255,0,0,255],[0,255,0,255],[0,0,255,255]], dtype = np.ubyte)
        self.plot_colourmap =  pg.ColorMap(val,colour)
        val = [0.0,0.1,0.2]
        colour = np.array([[0,255,0,255],[0,255,0,255],[255,0,0,255]], dtype = np.ubyte)
        self.level_colourmap = pg.ColorMap(val,colour)
     
    def set_input_limits(self,linebox,low,high,in_type):
        val = in_type(linebox.text())
        print(val)
        linebox.setText( str(min(max(val,low),high)) )
    
    def toggle_trigger(self,string):
        try:
            val = int(string)
        except:
            val = -1
        
        if val == -1:
            self.RecUI.rec_boxes[3].setEnabled(False)
            self.RecUI.rec_boxes[4].setEnabled(False)
        else:
            self.RecUI.rec_boxes[3].setEnabled(True)
            self.RecUI.rec_boxes[4].setEnabled(True)
        
#----------------------OVERRIDDEN METHODS------------------------------------
    def resizeEvent(self, event):
        try:
            if self.chan_toggle_ext.isVisible():
                self.toggle_ext_toggling(toggle = True)
        except:
            pass

    # The method to call when the mainWindow is being close       
    def closeEvent(self,event):
        if self.plottimer.isActive():
            self.plottimer.stop()
            
        self.done.emit()
        self.rec.close()
        self.dataSaved.disconnect()
        event.accept()
        self.deleteLater()
            
#----------------------WIDGET CLASSES------------------------------------            
class BaseWidget(QWidget):
    def __init__(self, *arg, **kwarg):
        super().__init__(*arg, **kwarg)
        self.initUI()
        self.setObjectName('subWidget')
       
    def paintEvent(self, evt):
        super().paintEvent(evt)
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        s = self.style()
        s.drawPrimitive(QStyle.PE_Widget, opt, p, self) 
    
    def initUI(self):
        pass
            
class ChanToggleUI(BaseWidget):
    def initUI(self):
        # Set up the channel tickboxes widget
        chans_toggle_layout = QVBoxLayout(self)
        
        # Make the button tickboxes scrollable
        scroll = QScrollArea()
        
        self.channels_box = QWidget(scroll)
        self.checkbox_layout = QGridLayout(self.channels_box)
        
        # Set up the QbuttonGroup to manage the Signals
        self.chan_btn_group = QButtonGroup(self.channels_box)
        self.chan_btn_group.setExclusive(False)
                
        scroll.setWidget(self.channels_box)
        scroll.setWidgetResizable(True)
        
        chans_toggle_layout.addWidget(scroll)
        
        # Set up the selection toggle buttons
        sel_btn_layout = QGridLayout()    
        self.sel_all_btn = QPushButton('Select All', self)
        self.desel_all_btn = QPushButton('Deselect All',self)
        self.inv_sel_btn = QPushButton('Invert Selection',self)
        for y,btn in zip((0,1,2),(self.sel_all_btn,self.desel_all_btn,self.inv_sel_btn)):
            btn.resize(btn.sizeHint())
            sel_btn_layout.addWidget(btn,y,0)
        
        self.chan_text = ChanLineText(self)
        sel_btn_layout.addWidget(self.chan_text,0,1)
        self.toggle_ext_button = QPushButton('>>',self)
        sel_btn_layout.addWidget(self.toggle_ext_button,1,1)
        
        chans_toggle_layout.addLayout(sel_btn_layout)
        #chanUI_layout.addLayout(chans_settings_layout)
        
        self.sel_all_btn.clicked.connect(lambda: self.toggle_all_checkboxes(Qt.Checked))
        self.desel_all_btn.clicked.connect(lambda: self.toggle_all_checkboxes(Qt.Unchecked))
        self.inv_sel_btn.clicked.connect(self.invert_checkboxes)
        
    def invert_checkboxes(self):
        for btn in self.channels_box.findChildren(QCheckBox):
            btn.click()
         
    def toggle_all_checkboxes(self,state):
        for btn in self.channels_box.findChildren(QCheckBox):
            if not btn.checkState() == state:
                btn.click()
        
class ChanConfigUI(BaseWidget):
    def initUI(self):
        chans_prop_layout = QVBoxLayout(self)
        chans_prop_layout.setContentsMargins(5,5,5,5)
        #chans_prop_layout.setSpacing(10)
        
        chan_num_col_layout = QGridLayout()
        
        self.chans_num_box = QComboBox(self)        
        self.hold_tickbox = QCheckBox('Hold',self)
        chan_num_col_layout.addWidget(QLabel('Channel',self),0,0)
        chan_num_col_layout.addWidget(self.chans_num_box,0,1)
        chan_num_col_layout.addWidget(self.hold_tickbox,0,2)
        
        self.colbox = pg.ColorButton(self,(0,255,0))
        self.defcol_btn = QPushButton('Reset Colour',self)
        self.meta_btn = QPushButton('Channel Info',self)
        chan_num_col_layout.addWidget(QLabel('Colour',self),1,0)
        chan_num_col_layout.addWidget(self.colbox,1,1)
        chan_num_col_layout.addWidget(self.defcol_btn,1,2)
        chan_num_col_layout.addWidget(self.meta_btn,2,0,1,3)
        
        chans_prop_layout.addLayout(chan_num_col_layout)
        
        chan_settings_layout = QVBoxLayout()
        chan_settings_layout.setSpacing(0)
        
                
        self.time_offset_config = []
        self.fft_offset_config = []
        
        for set_type in ('Time','DFT'):
            settings_gbox = QGroupBox(set_type, self)
            settings_gbox.setFlat(True)
            gbox_layout = QGridLayout(settings_gbox)
            row = 0
            for c in ['XMove','YMove']:
                cbox = pg.SpinBox(parent= settings_gbox, value=0.0, bounds=[None, None],step = 0.1)
                stepbox = pg.SpinBox(parent= settings_gbox, value=0.1, bounds=[None, None],step = 0.001)
                stepbox.valueChanged.connect(fct.partial(self.set_offset_step,cbox))
                
                gbox_layout.addWidget(QLabel(c,self),row,0)
                gbox_layout.addWidget(cbox,row,1)
                gbox_layout.addWidget(stepbox,row,2)
                if set_type == 'Time':
                    self.time_offset_config.append(cbox)
                elif set_type == 'DFT':
                    self.fft_offset_config.append(cbox)
                row += 1   
            settings_gbox.setLayout(gbox_layout)
            chan_settings_layout.addWidget(settings_gbox)
             
        chans_prop_layout.addLayout(chan_settings_layout)
        
    def set_offset_step(self,cbox,num):
        cbox.setSingleStep(num)

class DevConfigUI(BaseWidget):
    def initUI(self):
         # Set the device settings form
        config_form = QFormLayout(self)
        config_form.setSpacing(2)
        
        # Set up the device type radiobuttons group
        self.typegroup = QGroupBox('Input Type', self)
        typelbox = QHBoxLayout(self.typegroup)
        pyaudio_button = QRadioButton('SoundCard',self.typegroup)
        NI_button = QRadioButton('NI',self.typegroup)
        typelbox.addWidget(pyaudio_button)
        typelbox.addWidget(NI_button)
        
        # Set that to the layout of the group
        self.typegroup.setLayout(typelbox)
        
        # TODO: Give id to the buttons?
        # Set up QbuttonGroup to manage the buttons' Signals
        self.typebtngroup = QButtonGroup(self)
        self.typebtngroup.addButton(pyaudio_button)
        self.typebtngroup.addButton(NI_button)
        print('a',self.typebtngroup)
        
        config_form.addRow(self.typegroup)
        
        # Add the remaining settings to Acquisition settings form
        configs = ['Source','Rate','Channels','Chunk Size','Number of Chunks']
        self.configboxes = []
        
        for c in configs:
            if c == 'Source':
                cbox = QComboBox(self)
                config_form.addRow(QLabel(c,self),cbox)
                self.configboxes.append(cbox)
                
            else:
                cbox = QLineEdit(self)
                config_form.addRow(QLabel(c,self),cbox)
                self.configboxes.append(cbox)  
        
        # Add a button to device setting form
        self.config_button = QPushButton('Set Config', self)
        config_form.addRow(self.config_button)
    
class StatusUI(BaseWidget):
    def initUI(self):
        stps_layout = QHBoxLayout(self)
    
        # Set up the status bar
        self.statusbar = QStatusBar(self)
        self.statusbar.showMessage('Streaming')
        self.statusbar.clearMessage()
        stps_layout.addWidget(self.statusbar)
        
        self.resetView = QPushButton('Reset View',self)
        self.resetView.resize(self.resetView.sizeHint())
        stps_layout.addWidget(self.resetView)
        self.togglebtn = QPushButton('Pause',self)
        self.togglebtn.resize(self.togglebtn.sizeHint())
        stps_layout.addWidget(self.togglebtn)
        self.sshotbtn = QPushButton('Get Snapshot',self)
        self.sshotbtn.resize(self.sshotbtn.sizeHint())
        stps_layout.addWidget(self.sshotbtn)
        
class RecUI(BaseWidget):
    def initUI(self):
        rec_settings_layout = QFormLayout(self)
        
        rec_title = QLabel('Recording Settings', self)
        rec_title.setStyleSheet('''
                                font: 18pt;
                                ''')
        rec_settings_layout.addRow(rec_title)
        # Add the recording setting UIs with the Validators
        configs = ['Samples','Seconds','Pretrigger','Ref. Channel','Trig. Level']
        default_values = [None,'1.0', '200','0','0.0']
        validators = [QIntValidator(1,MAX_SAMPLE),None,QIntValidator(-1,MAX_SAMPLE),
                      None,QDoubleValidator(0,5,2)]
        
        self.rec_boxes = []
        for c,v,vd in zip(configs,default_values,validators):
            if c == 'Ref. Channel':
                cbox = QComboBox(self)
            else:
                cbox = QLineEdit(self)
                cbox.setText(v)
                if vd:
                    cbox.setValidator(vd)
                
            rec_settings_layout.addRow(QLabel(c,self),cbox)
            self.rec_boxes.append(cbox)  

        # Add the record and cancel buttons
        rec_buttons_layout = QHBoxLayout()
        
        self.recordbtn = QPushButton('Record',self)
        self.recordbtn.resize(self.recordbtn.sizeHint())
        rec_buttons_layout.addWidget(self.recordbtn)
        self.cancelbtn = QPushButton('Cancel',self)
        self.cancelbtn.resize(self.cancelbtn.sizeHint())
        self.cancelbtn.setDisabled(True)
        rec_buttons_layout.addWidget(self.cancelbtn)
        
        rec_settings_layout.addRow(rec_buttons_layout)
        
class AdvToggleUI(BaseWidget):
    def initUI(self):
        self.setAutoFillBackground(True)
        lay = QVBoxLayout(self)
        
        self.close_ext_toggle = QPushButton('<<',self)
        self.chan_text2 = ChanLineText(self)
        self.chan_text3 = QLineEdit(self)
        self.chan_text4 = QLineEdit(self)
        self.search_status = QStatusBar(self)
        self.search_status.setSizeGripEnabled(False)
        code_warning = QLabel('**Toggling by expression or tags**')
        code_warning.setWordWrap(True)
        lay.addWidget(self.close_ext_toggle)
        lay.addWidget(code_warning)
        lay.addWidget(QLabel('Expression:'))
        lay.addWidget(self.chan_text2)
        
        lay.addWidget(QLabel('Hashtag Toggle:'))
        lay.addWidget(self.chan_text3)
        lay.addWidget(QLabel('Channel(s) Toggled:'))
        lay.addWidget(self.chan_text4)
        lay.addWidget(self.search_status)
                
        self.search_status.showMessage('Awaiting...')        
        
if __name__ == '__main__':
    app = 0 
    app = QApplication(sys.argv)
    w = LiveplotApp()
    sys.exit(app.exec_())           

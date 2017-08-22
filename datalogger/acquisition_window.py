# -*- coding: utf-8 -*-
"""
Created on Wed Jul  5 13:12:34 2017

@author: eyt21
"""
import sys,traceback
from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QMainWindow,
    QPushButton, QDesktopWidget,QStatusBar, QLabel,QLineEdit, QFormLayout,
    QGroupBox,QRadioButton,QSplitter,QFrame, QComboBox,QScrollArea,QGridLayout,
    QCheckBox,QButtonGroup,QTextEdit,QApplication,QStackedLayout)
from PyQt5.QtGui import (QValidator,QIntValidator,QDoubleValidator,QColor)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint

import pyqtgraph as pg

import copy
import numpy as np
from numpy.fft import rfft
import functools as fct
import math

from datalogger.acquisition.RecordingUIs import (ChanToggleUI,ChanConfigUI,DevConfigUI,
                                                 StatusUI,RecUI,AdvToggleUI)
from datalogger.acquisition.ChanMetaWin import ChanMetaWin

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
from datalogger.analysis.transfer_function import compute_transfer_function

from datalogger.api import channel as ch
from datalogger.api.pyqtgraph_extensions import CustomPlotWidget

from datalogger.api.toolbox import Toolbox, MasterToolbox



# GLOBAL CONSTANTS
PLAYBACK = False    # Whether to playback the stream
MAX_SAMPLE = 1e9    # Recording Sample max size limit
WIDTH = 900         # Window width
HEIGHT = 600        # Window height
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
        self.setGeometry(400,300,WIDTH,HEIGHT)
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
           
        self.past_tf_data = []
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
    #-------------------- ALL TOOLBOXES ------------------------------
        self.stream_toolbox = MasterToolbox()
        self.recording_toolbox = MasterToolbox()
        
    #---------------------CHANNEL TOGGLE UI----------------------------------
        self.stream_tools = Toolbox('left',self.main_widget)
        
        self.chan_toggles = QWidget(self.main_widget)
        chan_toggle_layout = QVBoxLayout(self.chan_toggles)
        
        self.chantoggle_UI = ChanToggleUI(self.main_widget)        
        self.ResetChanBtns()
        self.chantoggle_UI.toggleChanged.connect(self.display_channel_plots)
        self.chantoggle_UI.lineToggled.connect(self.chan_line_toggle)
        
        chan_toggle_layout.addWidget(self.chantoggle_UI)
        
    #---------------------------ADDITIONAL UIs----------------------------
        self.chan_toggle_ext = AdvToggleUI(self.main_widget)
        self.chan_toggle_ext.chan_text2.returnPressed.connect(self.chan_line_toggle)
        chan_toggle_layout.addWidget(self.chan_toggle_ext)
        
    #----------------CHANNEL CONFIGURATION WIDGET---------------------------
        self.chanconfig_UI = ChanConfigUI(self.main_widget)
        
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
    #----------------DEVICE CONFIGURATION WIDGET---------------------------   
        self.devconfig_UI = DevConfigUI(self.main_widget)
        NI_btn = self.devconfig_UI.typegroup.findChildren(QRadioButton)[1]
        if not NI_drivers:
            NI_btn.setDisabled(True)
        
        self.devconfig_UI.recorderSelected.connect(self.display_sources)
        self.devconfig_UI.configRecorder.connect(self.ResetRecording)
        
        self.stream_tools.addTab(self.chan_toggles,'Channel Toggle')
        self.stream_tools.addTab(self.chanconfig_UI,'Channel Config')
        self.stream_tools.addTab(self.devconfig_UI,'Device Config')
        self.stream_toolbox.add_toolbox(self.stream_tools)
        
    #----------------------PLOT + STATUS WIDGETS------------------------------------ 
        self.mid_splitter = QSplitter(self.main_widget,orientation = Qt.Vertical)
    
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
        
        self.stats_UI = StatusUI(self.mid_splitter)
        
        self.stats_UI.statusbar.messageChanged.connect(self.default_status)
        self.stats_UI.resetView.pressed.connect(self.ResetSplitterSizes)
        self.stats_UI.togglebtn.pressed.connect(lambda: self.toggle_rec())
        self.stats_UI.sshotbtn.pressed.connect(self.get_snapshot)
        
        self.mid_splitter.addWidget(self.timeplotcanvas)
        self.mid_splitter.addWidget(self.fftplotcanvas)
        self.mid_splitter.addWidget(self.stats_UI)
        self.mid_splitter.setCollapsible (2, False)
        
    #---------------------------RECORDING WIDGET-------------------------------
        self.right_splitter = QSplitter(self.main_widget,orientation = Qt.Vertical)
        self.recording_tools = Toolbox('right',self.main_widget)
        
        self.RecUI = RecUI(self.main_widget)
        self.RecUI.set_recorder(self.rec)
        
        # Connect the sample and time input check
        self.RecUI.rec_boxes[2].editingFinished.connect(lambda: self.set_input_limits(self.RecUI.rec_boxes[2],-1,self.rec.chunk_size,int))
        self.RecUI.rec_boxes[2].textEdited.connect(self.toggle_trigger)
        self.RecUI.rec_boxes[4].textEdited.connect(self.change_threshold)

        self.RecUI.startRecording.connect(self.start_recording)
        self.RecUI.cancelRecording.connect(self.cancel_recording)
       
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
        
        self.recording_tools.addTab(self.right_splitter,'Record Time Series')
        self.recording_toolbox.add_toolbox(self.recording_tools)
        
        
    #------------------------FINALISE THE LAYOUT-----------------------------
        main_layout.addWidget(self.stream_toolbox)
        main_layout.addWidget(self.mid_splitter)
        main_layout.addWidget(self.recording_toolbox)
        main_layout.setStretchFactor(self.stream_toolbox, 0)
        main_layout.setStretchFactor(self.mid_splitter, 1)
        main_layout.setStretchFactor(self.recording_toolbox, 0)
        
        self.ResetSplitterSizes()
        
    #-----------------------EXPERIMENTAL STYLING---------------------------- 
        #self.main_splitter.setFrameShape(QFrame.Panel)
        #self.main_splitter.setFrameShadow(QFrame.Sunken)
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
    '''
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
    ''' 
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
        for i in range(snapshot.shape[1]):
            self.live_chanset.set_channel_data(i,'time_series',snapshot[:,i])
                
        self.live_chanset.set_channel_metadata( tuple(range(snapshot.shape[1])),
                                                   {'sample_rate':self.rec.rate})
        self.save_data()
        self.stats_UI.statusbar.showMessage('Snapshot Captured!', 1500)
        
    
#---------------------------RECORDING WIDGET-------------------------------    
    # Start the data recording        
    def start_recording(self):
        rec_configs = self.RecUI.get_record_config()
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
        
        for UIs in self.RecUI.children():
            try:
                UIs.setDisabled(True)
            except AttributeError:
                continue       
        self.RecUI.cancelbtn.setEnabled(True)
    
    # Stop the data recording and transfer the recorded data to main window    
    def stop_recording(self):
        #self.rec.recording = False
        for btn in self.main_widget.findChildren(QPushButton):
            btn.setEnabled(True)
            
        self.RecUI.cancelbtn.setDisabled(True)
        data = self.rec.flush_record_data()
        
        for i in range(data.shape[1]):
                self.live_chanset.set_channel_data(i,'time_series',data[:,i])
        
        rec_mode = self.RecUI.get_recording_mode()
        if rec_mode == 'TF Avg.':
            ft_datas = []
            tf_datas = []
            for i in range(data.shape[1]):
                ft = rfft(data[:,i])
                self.live_chanset.add_channel_dataset(i,'fft',ft)
                ft_datas.append(ft)
                
            in_chan = self.RecUI.input_chan_box.currentIndex()
            input_chan_data = ft_datas[in_chan]
            for i in range(data.shape[1]):
                tf,_ = compute_transfer_function(input_chan_data,ft_datas[i])
                tf_datas.append(tf)
                #self.live_chanset.set_channel_data(i,'spectrum',avg_tf)
                
            self.past_tf_data.append(tf_datas)
            print('Avg : %i' % len(self.past_tf_data))
            #avg_tf = np.array(self.past_tf_data).mean(axis=2)
            #for i in range(data.shape[1]): 
            #    self.live_chanset.set_channel_data(i,'spectrum',avg_tf[i,:])
            
        elif rec_mode == 'TF Grid':
            pass
        else:
            pass
       
        self.live_chanset.set_channel_metadata( tuple(range(data.shape[1])),
                                                   {'sample_rate':self.rec.rate})
        self.save_data()
        self.stats_UI.statusbar.clearMessage() 
        for UIs in self.RecUI.children():
            try:
                UIs.setEnabled(True)
            except AttributeError:
                continue
    
    # Cancel the data recording
    def cancel_recording(self):
        self.rec.record_cancel()
        for btn in self.main_widget.findChildren(QPushButton):
            btn.setEnabled(True)
        for UIs in self.RecUI.children():
            try:
                UIs.setEnabled(True)
            except AttributeError:
                continue
        self.RecUI.cancelbtn.setDisabled(True)
        self.stats_UI.statusbar.clearMessage()
        
    
    
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
        except:
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))
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
            self.RecUI.set_recorder(self.rec)
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
        #self.main_splitter.setSizes([WIDTH*0.25,WIDTH*0.55,WIDTH*0.2]) 
        self.mid_splitter.setSizes([HEIGHT*0.48,HEIGHT*0.48,HEIGHT*0.04])
        self.right_splitter.setSizes([HEIGHT*0.05,HEIGHT*0.85])
        
    def update_chan_names(self):
        names = self.live_chanset.get_channel_metadata(tuple(range(self.rec.channels)),'name')
        for n,name in enumerate(names):
            chan_btn = self.chantoggle_UI.chan_btn_group.button(n)
            chan_btn.setText(name)
        
#----------------------- DATA TRANSFER METHODS -------------------------------    
    # Transfer data to main window      
    def save_data(self):
        print('Saving data...')
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
            

if __name__ == '__main__':
    app = 0 
    app = QApplication(sys.argv)
    w = LiveplotApp()
    sys.exit(app.exec_())           

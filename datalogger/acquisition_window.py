# -*- coding: utf-8 -*-
"""
Created on Wed Jul  5 13:12:34 2017

@author: eyt21

This module contains the application to stream and record data.
It contains widgets to configure and toggle channel plots,
configure recording device, and configure recording.
It displays a time domain plot, a frequecy domain plot (DFT),
and a channel levels plot, all in real time.

Further information on the functionality of each widget can be found in 
RecordingUI.

The application is meant to be used with the analysis window application,
because recorded data are transfer to that window for analysis.

However, the application can work standalone, but the recorded data will
go nowhere.

Attribute
----------
NI_DRIVERS: Bool
    Indicates whether NIDAQmx drivers and pyDAQmx module are installed
    when attempting to import NIRecorder module
    These are required to interface with a National Instrument hardware.
PLAYBACK: Bool
    Indicates whether to play the streaming audio, only works with SoundCard
WIDTH: Int
    Width of the application window
HEIGHT: Int
    Height of the application window
"""
import sys,traceback
from PyQt5.QtWidgets import (QWidget,QHBoxLayout,QMainWindow,QPushButton,
                             QDesktopWidget,QRadioButton,QSplitter,
                             QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

import pyqtgraph as pg

import copy
import numpy as np
from numpy.fft import rfft

from datalogger.acquisition.RecordingUIs import (ChanToggleUI,ChanConfigUI,DevConfigUI,
                                                 StatusUI,RecUI)
from datalogger.acquisition.RecordingGraph import TimeLiveGraph,FreqLiveGraph,LevelsLiveGraph
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
from datalogger.analysis.frequency_domain import (compute_transfer_function,
                                                   compute_autospec,compute_crossspec)

from datalogger.api.channel import ChannelSet
from datalogger.api.toolbox import Toolbox, MasterToolbox

# GLOBAL CONSTANTS
PLAYBACK = False    # Whether to playback the stream
WIDTH = 900         # Window width
HEIGHT = 600        # Window height

#++++++++++++++++++++++++ The LivePlotApp Class +++++++++++++++++++++++++++
class LiveplotApp(QMainWindow):
    """
    This is the window that acts as the central hub for all the widgets.
    Contains a left Toolbox for streaming configuration and a right Toolbox
    for recording configuration.
    The center contain the Time Domain and Frequency Domain Plots, along with a
    status bar below them. The channel levels plot is placed in the right Toolbox.
    
    The widgets communicate with each other using the pyqt Signal and Slot method,
    so most callback functions are self-contained in the respective widget. 
    However, some callback function are still present in the main body, mostly
    functions to handle the streaming and the recording processes.
    
    Attributes
    ----------
    dataSaved: pyqtSignal
        Emitted when recorded data 
    done: pyqtSignal
        Emitted when the window is closed
    playing: Bool
        Indicate whether the stream is playing
    rec: Recorder object
         Object which handles the streaming and recording
         See documentation for Recorder classes
    """
    dataSaved = pyqtSignal(int)
    done = pyqtSignal()
   
    def __init__(self,parent = None):
        """
        Initialise and construct the window application.
        
        Parameter
        ----------
        parent: object
            The object which the window interacts with
            e.g. The analysis window
        """
        super().__init__()
        self.parent = parent
        
        # Set window parameter
        self.setGeometry(400,300,WIDTH,HEIGHT)
        self.setWindowTitle('LiveStreamPlot')
        
        self.meta_window = None
        
        # Set recorder object
        self.playing = False
        self.rec = mR.Recorder(channels = 2,
                                num_chunk = 6,
                                device_name = 'Line (U24XL with SPDIF I/O)')
        # Set up the TimeSeries and FreqSeries
        self.timedata = None 
        self.freqdata = None
        
        # Set up tallies for the average transfer function calculation  
        self.autospec_in_tally = []
        self.autospec_out_tally = []
        self.crossspec_tally = []
        
        try:
            # Construct UI        
            self.initUI()
        except Exception:
            # If it fails, show the window and stop
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))
            self.show()
            return
        
        # Connect the recorder Signals
        self.connect_rec_signals()
        
        # Attempt to start streaming
        self.init_and_check_stream()
            
        # Center and show window
        self.adjust_position()
        self.setFocus()
        self.show()
     
    def initUI(self):
        """
        Construct the window by calling the widgets classes, and any additional
        widgets (such as Qsplitters, Toolbox)
        Then, perform the signal connection among the widgets.
        Also sets up the update timer for the streaming.
        Lastly, finalise the plots and misc. items.
        
        There is also an experimental styling section just after the UI
        construction.
        """
        # Set up the main widget        
        self.main_widget = QWidget(self)
        main_layout = QHBoxLayout(self.main_widget)
    #------------------------- STREAM TOOLBOX ------------------------------
        self.stream_toolbox = MasterToolbox()
        self.stream_tools = Toolbox('left',self.main_widget)
        self.stream_toolbox.add_toolbox(self.stream_tools)
        self.chantoggle_UI = ChanToggleUI(self.main_widget)        
        self.chanconfig_UI = ChanConfigUI(self.main_widget)
        self.devconfig_UI = DevConfigUI(self.main_widget)
        self.devconfig_UI.set_recorder(self.rec)
        self.devconfig_UI.config_setup()
        NI_btn = self.devconfig_UI.typegroup.findChildren(QRadioButton)[1]
        if not NI_drivers:
            NI_btn.setDisabled(True)
        self.stream_tools.addTab(self.chantoggle_UI,'Channel Toggle')
        self.stream_tools.addTab(self.chanconfig_UI,'Channel Config')
        self.stream_tools.addTab(self.devconfig_UI,'Device Config')
        main_layout.addWidget(self.stream_toolbox)
        main_layout.setStretchFactor(self.stream_toolbox, 0)
        
    #---------------------------PLOT + STATUS WIDGETS-----------------------------
        self.mid_splitter = QSplitter(self.main_widget,orientation = Qt.Vertical)
        self.timeplot = TimeLiveGraph(self.mid_splitter)
        self.freqplot = FreqLiveGraph(self.mid_splitter)  
        self.stats_UI = StatusUI(self.mid_splitter)
        self.mid_splitter.addWidget(self.timeplot)
        self.mid_splitter.addWidget(self.freqplot)
        self.mid_splitter.addWidget(self.stats_UI)
        self.mid_splitter.setCollapsible (2, False)
        main_layout.addWidget(self.mid_splitter)
        main_layout.setStretchFactor(self.mid_splitter, 1)
        
    #---------------------------RECORDING TOOLBOX-------------------------------
        self.recording_toolbox = MasterToolbox()
        self.recording_tools = Toolbox('right',self.main_widget)
        self.recording_toolbox.add_toolbox(self.recording_tools)
        self.right_splitter = QSplitter(self.main_widget,orientation = Qt.Vertical)
        self.RecUI = RecUI(self.main_widget)
        self.RecUI.set_recorder(self.rec)
        self.right_splitter.addWidget(self.RecUI)
        self.levelsplot = LevelsLiveGraph(self.rec,self.right_splitter)        
        self.right_splitter.addWidget(self.levelsplot)
        self.recording_tools.addTab(self.right_splitter,'Record Time Series')
        main_layout.addWidget(self.recording_toolbox)
        main_layout.setStretchFactor(self.recording_toolbox, 0)
        
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
        
    #----------------------SIGNAL CONNECTIONS---------------------------
        self.chantoggle_UI.sigToggleChanged.connect(self.timeplot.toggle_plotline)
        self.chantoggle_UI.sigToggleChanged.connect(self.freqplot.toggle_plotline)
        self.chanconfig_UI.chans_num_box.currentIndexChanged.connect(self.display_chan_config)        
        self.chanconfig_UI.meta_btn.clicked.connect(self.open_meta_window)
        self.chanconfig_UI.sigTimeOffsetChanged.connect(self.timeplot.set_offset)
        self.chanconfig_UI.sigFreqOffsetChanged.connect(self.freqplot.set_offset)
        self.chanconfig_UI.sigHoldChanged.connect(self.timeplot.set_sig_hold)
        self.chanconfig_UI.sigColourChanged.connect(self.timeplot.set_plot_colour)
        self.chanconfig_UI.sigColourChanged.connect(self.freqplot.set_plot_colour)
        self.chanconfig_UI.sigColourChanged.connect(self.levelsplot.set_plot_colour)
        self.chanconfig_UI.sigColourReset.connect(self.timeplot.reset_default_colour)
        self.chanconfig_UI.sigColourReset.connect(self.freqplot.reset_default_colour)
        self.chanconfig_UI.sigColourReset.connect(self.levelsplot.reset_default_colour)
        self.devconfig_UI.configRecorder.connect(self.ResetRecording)
        self.timeplot.plotColourChanged.connect(self.chanconfig_UI.set_colour_btn)
        self.freqplot.plotColourChanged.connect(self.chanconfig_UI.set_colour_btn)
        self.levelsplot.plotColourChanged.connect(self.chanconfig_UI.set_colour_btn)
        self.levelsplot.thresholdChanged.connect(self.RecUI.rec_boxes[4].setText)
        self.stats_UI.statusbar.messageChanged.connect(self.default_status)
        self.stats_UI.resetView.pressed.connect(self.ResetSplitterSizes)
        self.stats_UI.togglebtn.pressed.connect(lambda: self.toggle_rec())
        self.stats_UI.sshotbtn.pressed.connect(self.get_snapshot)
        self.RecUI.rec_boxes[4].textEdited.connect(self.levelsplot.change_threshold)
        self.RecUI.startRecording.connect(self.start_recording)
        self.RecUI.cancelRecording.connect(self.cancel_recording)
        self.RecUI.undoLastTfAvg.connect(self.undo_tf_tally)
        self.RecUI.clearTfAvg.connect(self.remove_tf_tally)
    #---------------------------RESETTING METHODS---------------------------
        self.ResetMetaData()   
        self.ResetChanBtns()
        self.ResetPlots()
        self.ResetChanConfigs()
        self.levelsplot.reset_channel_levels()
        self.ResetSplitterSizes()
    #-----------------------FINALISE THE MAIN WIDGET------------------------- 
        #Set the main widget as central widget
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        
        # Set up a timer to update the plot
        self.plottimer = QTimer(self)
        self.plottimer.timeout.connect(self.update_line)
        #self.plottimer.timeout.connect(self.update_chanlvls)
        self.plottimer.start(self.rec.chunk_size*1000//self.rec.rate)
        
        self.show()
        
    def adjust_position(self):
        """
        If it has a parent, adjust its position to be slightly out of the parent
        window towards the left
        """
        if self.parent:
            pr = self.parent.frameGeometry()
            qr = self.frameGeometry()
            self.move(pr.topLeft())
            self.move(qr.left()/2,qr.top())   
            
#----------------CHANNEL CONFIGURATION WIDGET---------------------------    
    def display_chan_config(self, arg):
        """
        Displays the channel plot offsets, colours, and signal holding.
        """
        # This function is here because it is easier for channel config to
        # get data from the plot widgets
        if type(arg) == pg.PlotDataItem:
            num = self.timeplot.check_line(arg)
            if not num == None:
                num = self.freqplot.check_line(arg)
                self.chanconfig_UI.chans_num_box.setCurrentIndex(num)
        else:
            num = arg
        
        self.chanconfig_UI.colbox.setColor(self.timeplot.plot_colours[num])
        self.chanconfig_UI.time_offset_config[0].setValue(self.timeplot.plot_xoffset[num])
        self.chanconfig_UI.time_offset_config[1].setValue(self.timeplot.plot_yoffset[num])
        self.chanconfig_UI.hold_tickbox.setCheckState(self.timeplot.sig_hold[num])
        self.chanconfig_UI.fft_offset_config[0].setValue(self.freqplot.plot_xoffset[num])
        self.chanconfig_UI.fft_offset_config[1].setValue(self.freqplot.plot_yoffset[num])
   
    def open_meta_window(self):
        """
        Open the metadata window
        """
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
        """
        Callback when the metadata window is closed
        """
        self.meta_window = None
        self.update_chan_names()

#----------------------PLOT WIDGETS-----------------------------------              
    # Updates the plots    
    def update_line(self):
        """
        Callback to update the time domain and frequency domain plot
        """
        # Get the buffer
        data = self.rec.get_buffer()
        
        # Take the last chunk for the levels plot
        currentdata = data[len(data)-self.rec.chunk_size:,:]
        currentdata -= np.mean(currentdata)
        rms = np.sqrt(np.mean(currentdata ** 2,axis = 0))
        maxs = np.amax(abs(currentdata),axis = 0)
        self.levelsplot.set_channel_levels(rms,maxs)
        
        # Prepare the window and weightage for FFT plot
        window = np.hanning(data.shape[0])
        weightage = np.exp(2* self.timedata / self.timedata[-1])
        
        # Update each plot item's data + level peaks
        for i in range(data.shape[1]):
            plotdata = data[:,i].reshape((len(data[:,i]),))
            
            # Check for zero crossing if needed
            zc = 0
            if self.timeplot.sig_hold[i] == Qt.Checked:
                avg = np.mean(plotdata);
                zero_crossings = np.where(np.diff(np.sign(plotdata-avg))>0)[0]
                if zero_crossings.shape[0]:
                    zc = zero_crossings[0]+1
            
            self.timeplot.update_line(i,x = self.timedata[:len(plotdata)-zc] ,y = plotdata[zc:])
            fft_data = rfft(plotdata* window * weightage)
            psd_data = abs(fft_data)** 0.5
            self.freqplot.update_line(i,x = self.freqdata ,y = psd_data)
            self.levelsplot.set_peaks(i,maxs[i])
            
#-------------------------STATUS BAR WIDGET--------------------------------
    def toggle_rec(self,stop = None):
        """
        Callback to pause/resume the stream, unless explicitly specified to stop or not
        
        Parameter
        ----------
        stop: Bool
            Specify whether to stop the stream. None to toggle the current state
        """
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
        """
        Callback to take the current buffer data and send it out to parent window
        """
        snapshot = self.rec.get_buffer()
        for i in range(snapshot.shape[1]):
            self.live_chanset.set_channel_data(i,'time_series',snapshot[:,i])
                
        self.live_chanset.set_channel_metadata( tuple(range(snapshot.shape[1])),
                                                   {'sample_rate':self.rec.rate})
        self.save_data()
        self.stats_UI.statusbar.showMessage('Snapshot Captured!', 1500)

    def default_status(self,msg):
        """
        Callback to set the status message to the default messages 
        if it is empty (ie when cleared)
        """
        # Placed here because it accesses self.playing (might change it soon?)
        if not msg:
            if self.playing:
                self.stats_UI.statusbar.showMessage('Streaming')
            else:
                self.stats_UI.statusbar.showMessage('Stream Paused')
                
    
#---------------------------RECORDING WIDGET-------------------------------           
    def start_recording(self):
        """
        Callback to start the data recording  
        """
        success = False
        rec_configs = self.RecUI.get_record_config()
        if rec_configs[2]>=0:
            # Set up the trigger if specified
            if self.rec.trigger_start(posttrig = rec_configs[0],
                                      duration = rec_configs[1],
                                      pretrig = rec_configs[2],
                                      channel = rec_configs[3],
                                      threshold = rec_configs[4]):
                success = True
                self.stats_UI.statusbar.showMessage('Trigger Set!')
        else:
            # Record normally
            self.rec.record_init(samples = rec_configs[0], duration = rec_configs[1])
            if self.rec.record_start():
                success = True
                self.stats_UI.statusbar.showMessage('Recording...')
        if success:
            # Disable buttons
            for btn in [self.stats_UI.togglebtn, self.devconfig_UI.config_button, self.RecUI.recordbtn]:
                btn.setDisabled(True)
            self.RecUI.switch_rec_box.setDisabled(True)
            self.RecUI.spec_settings_widget.setDisabled(True)
            # Enable the cancel buttons
            self.RecUI.cancelbtn.setEnabled(True)
    
    #   
    def stop_recording(self):
        """
        Callback when the recording finishes.
        Process the data first, if specify, then transfer the data 
        to the parent window   
        """
        # Enable the buttons
        for btn in self.main_widget.findChildren(QPushButton):
            btn.setEnabled(True)
        # Disable the cancel button    
        self.RecUI.cancelbtn.setDisabled(True)
        
        # Get the recorded data and compute DFT
        data = self.rec.flush_record_data()
        ft_datas = np.zeros((int(data.shape[0]/2)+1,data.shape[1]),dtype = np.complex)
        for i in range(data.shape[1]):
            self.live_chanset.set_channel_data(i,'time_series',data[:,i])
            ft = rfft(data[:,i])
            self.live_chanset.add_channel_dataset(i,'spectrum',ft)
            ft_datas[:,i] = ft
        
        self.live_chanset.set_channel_metadata( tuple(range(data.shape[1])),
                                                   {'sample_rate':self.rec.rate})
        
        # Check recording mode
        rec_mode = self.RecUI.get_recording_mode()
        if rec_mode == 'Normal':
            # Send data normally
            self.live_chanset.add_channel_dataset(tuple(range(data.shape[1])),'TF',[])
            self.live_chanset.add_channel_dataset(tuple(range(data.shape[1])),'coherence',[])
            self.save_data(0)
        elif rec_mode == 'TF Avg.':
            # Compute the auto- and crossspectrum for average transfer function
            # while store them in the tally
            chans = list(range(self.rec.channels))
            in_chan = self.RecUI.get_input_channel()
            chans.remove(in_chan)
            input_chan_data = ft_datas[:,in_chan]
            
            # Check for incorrect data length with previous recorded data
            if not len(self.autospec_in_tally)==0: 
                if not input_chan_data.shape[0] == self.autospec_in_tally[-1].shape[0]:
                    print('Data shape does not match, you may have fiddle the settings')
                    print('Please either clear the past data, or revert the settings')
                    self.stats_UI.statusbar.clearMessage() 
                    self.RecUI.spec_settings_widget.setEnabled(True)
                    self.RecUI.switch_rec_box.setEnabled(True) 
                    return
                
            self.autospec_in_tally.append(compute_autospec(input_chan_data))
            
            autospec_out = np.zeros((ft_datas.shape[0],ft_datas.shape[1] - 1),dtype = np.complex)
            crossspec = np.zeros(autospec_out.shape,dtype = np.complex)
            for i,chan in enumerate(chans):
                autospec_out[:,i] = compute_autospec(ft_datas[:,chan])
                crossspec[:,i] = compute_crossspec(input_chan_data,ft_datas[:,chan])
             
            self.autospec_out_tally.append(autospec_out)
            self.crossspec_tally.append(crossspec)     
            auto_in_sum = np.array(self.autospec_in_tally).sum(axis = 0)
            auto_out_sum = np.array(self.autospec_out_tally).sum(axis = 0)
            cross_sum = np.array(self.crossspec_tally).sum(axis = 0)     
            for i,chan in enumerate(chans):
                tf_avg,cor = compute_transfer_function(auto_in_sum,auto_out_sum[:,i],cross_sum[:,i])
                self.live_chanset.add_channel_dataset(chan,'TF',tf_avg)
                self.live_chanset.add_channel_dataset(chan,'coherence',cor)
        
            # Update the average count and send the data
            self.RecUI.update_TFavg_count(len(self.autospec_in_tally))
            self.save_data(1)
            
        elif rec_mode == 'TF Grid':
            # TODO: Implement recording for grid transfer function
            pass
        else:
            # TODO?: Failsafe for unknown mode
            pass
       
        # Enable more widgets
        self.stats_UI.statusbar.clearMessage() 
        self.RecUI.spec_settings_widget.setEnabled(True)
        self.RecUI.switch_rec_box.setEnabled(True) 
            
    def undo_tf_tally(self):
        """
        Callback to remove the last autospectrum and crossspectrum in the tally  
        """
        if self.autospec_in_tally:
            self.autospec_in_tally.pop()
            self.autospec_out_tally.pop()
            self.crossspec_tally.pop()
        self.RecUI.update_TFavg_count(len(self.autospec_in_tally))
        
    def remove_tf_tally(self):
        """
        Callback to clear the autospectrum and crossspectrum tallies
        """
        if self.autospec_in_tally:
            self.autospec_in_tally = []
            self.autospec_out_tally = []
            self.crossspec_tally = []
        self.RecUI.update_TFavg_count(len(self.autospec_in_tally))
    
    # Cancel the data recording
    def cancel_recording(self):
        """
        Callback to cancel the recording and re-enable the UIs
        """
        self.rec.record_cancel()
        for btn in self.main_widget.findChildren(QPushButton):
            btn.setEnabled(True)
            
        self.RecUI.switch_rec_box.setEnabled(True) 
        self.RecUI.spec_settings_widget.setEnabled(True)
        self.RecUI.cancelbtn.setDisabled(True)
        self.stats_UI.statusbar.clearMessage()

#--------------------------- RESET METHODS-------------------------------------    
    def ResetRecording(self):
        """
        Reset the stream to the specified configuration, then
        calls upon other reset methods
        """
        # Spew errors to console at each major step of the resetting
        self.stats_UI.statusbar.showMessage('Resetting...')
        
        # Stop the update and Delete the stream
        self.playing = False
        self.plottimer.stop()
        self.rec.close()
        del self.rec
                
        try:    
            # Get Input from the Device Configuration UI
            Rtype, settings = self.devconfig_UI.read_device_config()
            # Reinitialise the recording object
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
            # Open the stream
            self.init_and_check_stream()
            # Reset channel configs
            self.ResetPlots()            
            self.levelsplot.reset_channel_peaks(self.rec)
            self.ResetChanConfigs()
            self.levelsplot.reset_channel_levels()
        except:
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))
            print('Cannot stream,restart the app')
        
        try:
            # Set the recorder reference to RecUI and devconfig_UI, and remove 
            # average transfer function tally
            self.RecUI.set_recorder(self.rec)
            self.devconfig_UI.set_recorder(self.rec)
            self.remove_tf_tally()
        except:
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))
            print('Cannot recording configs')

        # Reset metadata and change channel toggles and re-connect the signals
        self.ResetMetaData()
        self.ResetChanBtns()
        self.connect_rec_signals()
        
        # Restart the plot update timer
        self.plottimer.start(self.rec.chunk_size*1000//self.rec.rate)
        
    def ResetPlots(self):
        """
        Reset the plots
        """
        self.ResetXdata()
        
        self.timeplot.reset_plotlines()
        self.freqplot.reset_plotlines()
        
        for i in range(self.rec.channels):
            tplot = self.timeplot.plot()
            tplot.sigClicked.connect(self.display_chan_config)
            
            fplot = self.freqplot.plot()
            fplot.sigClicked.connect(self.display_chan_config)
            
        self.freqplot.plotItem.setRange(xRange = (0,self.freqdata[-1]),yRange = (0, 100*self.rec.channels))
        self.freqplot.plotItem.setLimits(xMin = 0,xMax = self.freqdata[-1],yMin = -20)
    
    def ResetXdata(self):
        """
        Reset the time and frequencies plot data
        """
        data = self.rec.get_buffer()
        self.timedata = np.arange(data.shape[0]) /self.rec.rate 
        self.freqdata = np.arange(int(data.shape[0]/2)+1) /data.shape[0] * self.rec.rate
  
    def ResetChanBtns(self):
        """
        Reset the amount of channel toggling buttons
        """
        self.chantoggle_UI.adjust_channel_checkboxes(self.rec.channels)            
        self.update_chan_names()                       
                
    def ResetChanConfigs(self):
        """
        Reset the channel plot configuration settings
        """
        self.timeplot.reset_offsets()
        self.timeplot.reset_plot_visible()
        self.timeplot.reset_colour()
        self.timeplot.reset_sig_hold()
        self.freqplot.reset_offsets()
        self.freqplot.reset_plot_visible()
        self.freqplot.reset_colour()
        self.levelsplot.reset_colour()

        self.chanconfig_UI.chans_num_box.clear()
        self.chanconfig_UI.chans_num_box.addItems([str(i) for i in range(self.rec.channels)])
        self.chanconfig_UI.chans_num_box.setCurrentIndex(0)
        
        self.display_chan_config(0)
    
    def ResetMetaData(self):
        """
        Reset the metadata
        """
        self.live_chanset = ChannelSet(self.rec.channels)
        self.live_chanset.add_channel_dataset(tuple(range(self.rec.channels)), 'time_series')
        
    def ResetSplitterSizes(self):
        """
        Reset the metadata
        """
        self.mid_splitter.setSizes([HEIGHT*0.48,HEIGHT*0.48,HEIGHT*0.04])
        self.right_splitter.setSizes([HEIGHT*0.05,HEIGHT*0.85])
        
    def update_chan_names(self):
        """
        Update the channel names, obtained from the ChannelSet
        """
        names = self.live_chanset.get_channel_metadata(tuple(range(self.rec.channels)),'name')
        for n,name in enumerate(names):
            chan_btn = self.chantoggle_UI.chan_btn_group.button(n)
            chan_btn.setText(name)
        
#----------------------- DATA TRANSFER METHODS -------------------------------    
         
    def save_data(self, tab_num = 0):
        """
        Transfer data to parent window
        
        Parameter
        ---------
        tab_num: Tab index to switch to in the parent window (specific for analysis window)
        """
        if self.parent:
            print('Saving data...')
            self.parent.cs = copy.copy(self.live_chanset)
            self.dataSaved.emit(tab_num)        
            print('Data saved!')

#-------------------------- STREAM METHODS ------------------------------------        
    def init_and_check_stream(self):
        """
        Attempts to initialise the stream
        """
        if self.rec.stream_init(playback = PLAYBACK):
            self.stats_UI.togglebtn.setEnabled(True)
            self.toggle_rec(stop = False)
            self.stats_UI.statusbar.showMessage('Streaming')
        else:
            self.stats_UI.togglebtn.setDisabled(True)
            self.toggle_rec(stop = True)
            self.stats_UI.statusbar.showMessage('Stream not initialised!')
            
    def connect_rec_signals(self):
        """
        Connects the signals from the recorder object
        """
        self.rec.rEmitter.recorddone.connect(self.stop_recording)
        self.rec.rEmitter.triggered.connect(self.stats_UI.trigger_message)
        #self.rec.rEmitter.newdata.connect(self.update_line)
        #self.rec.rEmitter.newdata.connect(self.update_chanlvls)
        
#----------------------OVERRIDDEN METHODS------------------------------------
    def closeEvent(self,event):
        """
        Reimplemented from QMainWindow
        Stops the update timer, disconnect any signals and delete self
        """
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

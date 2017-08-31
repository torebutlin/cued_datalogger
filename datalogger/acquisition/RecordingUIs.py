# -*- coding: utf-8 -*-
"""
Created on Tue Aug 22 11:19:29 2017
@author: eyt21

This module contains the widget classes to the acquisition window.
However, they are not limited to that window, and can be reused for other
window, like the analysis window.

Attribute
----------
NI_DRIVERS: Bool
    Indicates whether NIDAQmx drivers and pyDAQmx module are installed
    when attempting to import NIRecorder module
    The module is needed to check on the available National Instrument devices
MAX_SAMPLE: int
    Arbritrary maximum number of samples that can be recorded.

"""
from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout, QPushButton, 
                             QStatusBar,QLabel,QLineEdit, QFormLayout,
                             QGroupBox,QRadioButton, QComboBox,QScrollArea,
                             QGridLayout,QCheckBox,QButtonGroup,QTextEdit,
                             QStackedWidget)
from PyQt5.QtGui import QValidator,QIntValidator,QDoubleValidator,QPainter
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.Qt import QStyleOption,QStyle

import re
import pyqtgraph as pg
import functools as fct

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

MAX_SAMPLE = 1e9 

#==========================WIDGET CLASSES================================
#---------------------------BASE WIDGET------------------------------------            
class BaseWidget(QWidget):
    """
     A base widget reimplemented to allow custom styling.
     Pretty much identical to a normal QWidget
    """
    def __init__(self, *arg, **kwarg):
        """
        Reimplemented from QWidget
        """
        super().__init__(*arg, **kwarg)
        self.initUI()
        self.setObjectName('subWidget')
       
    def paintEvent(self, evt):
        """
        Reimplemented from QWidget.paintEvent()
        """
        super().paintEvent(evt)
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        s = self.style()
        s.drawPrimitive(QStyle.PE_Widget, opt, p, self) 
    
    def initUI(self):
        """
        Construct the UI, to be reimplemented.
        """
        pass
    
#-------------------------CHANNEL TOGGLE WIDGET-------------------------------          
class ChanToggleUI(BaseWidget):
    """
     A Channel Toggling widget.
     Contains: 
     - Checkboxes to toggle channel,
     - Buttons to select all, deselect all, and invert selection.
     - LineEdits to toggle by expression or tags
     
     Attributes
     ----------
     toggleChanged: pyqtsignal
         Emits when a channel toggle changes, 
         Sends out the channel num(int) and the state(bool)
     channels_box: QWidget
         The widget containing the checkboxes
     checkbox_layout: QGridLayout
         Defines the layout of the checkboxes
     chan_btn_group: QButtonGroup
         Widget to handle the checkboxes presses
     sel_all_btn:QPushButton
         'Select All' button
     desel_all_btn: QPushButton
         'Deselect All' button
     inv_sel_btn: QPushButton
         'Invert Selection' button
     chan_text: ChanLineText
         For toggling by expression
     chan_text2: QLineEdit
         For toggling by tags
     chan_text3: QLineEdit
         For displaying the channels toggled (may be changed to QLabel instead)
     search_status: QStatusBar
         For displaying whether the toggling is successful
    """
    sigToggleChanged = pyqtSignal(int,bool)
    
    def initUI(self):
        """
        Reimplemented from BaseWidget.
        """
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
        self.sel_all_btn = QPushButton('Select All', self)
        self.desel_all_btn = QPushButton('Deselect All',self)
        self.inv_sel_btn = QPushButton('Invert Selection',self)
        for btn in [self.sel_all_btn,self.desel_all_btn,self.inv_sel_btn]:
            btn.resize(btn.sizeHint())
            chans_toggle_layout.addWidget(btn)
        
        self.sel_all_btn.clicked.connect(lambda: self.toggle_all_checkboxes(Qt.Checked))
        self.desel_all_btn.clicked.connect(lambda: self.toggle_all_checkboxes(Qt.Unchecked))
        self.inv_sel_btn.clicked.connect(self.invert_checkboxes)
        
        self.chan_text = ChanLineText(self)
        self.chan_text2 = QLineEdit(self)
        self.chan_text3 = QLineEdit(self)
        self.search_status = QStatusBar(self)
        self.search_status.setSizeGripEnabled(False)
        code_warning = QLabel('**Toggling by expression or tags**')
        code_warning.setWordWrap(True)
        chans_toggle_layout.addWidget(code_warning)
        chans_toggle_layout.addWidget(QLabel('Expression:'))
        chans_toggle_layout.addWidget(self.chan_text)
        
        chans_toggle_layout.addWidget(QLabel('Hashtag Toggle:'))
        chans_toggle_layout.addWidget(self.chan_text2)
        chans_toggle_layout.addWidget(QLabel('Channel(s) Toggled:'))
        chans_toggle_layout.addWidget(self.chan_text3)
        chans_toggle_layout.addWidget(self.search_status)
                
        self.search_status.showMessage('Awaiting...')
        
        self.chan_btn_group.buttonClicked.connect(self.toggle_channel_plot)
        self.chan_text.returnPressed.connect(self.chan_line_toggle)
        
    def invert_checkboxes(self):
        """
        Callback to invert selection
        """
        for btn in self.channels_box.findChildren(QCheckBox):
            btn.click()
         
    def toggle_all_checkboxes(self,state):
        """
        Callback to select all or deselect all
        
        Parameters
        ----------
        state: int
            State of the checkboxes to be in (either Qt.Unchecked or Qt.Checked)
        """
        for btn in self.channels_box.findChildren(QCheckBox):
            if not btn.checkState() == state:
                btn.click()
                
    def adjust_channel_checkboxes(self, new_n_btns):
        """
        Add or delete checkboxes based on new number of buttons needed
        
        Parameters
        ----------
        new_n_btns: int
            New number of buttons required
        """
        for btn in self.chan_btn_group.buttons():
            btn.setCheckState(Qt.Checked)
            
        # Calculate the number of extra buttons required to add/delete
        old_n_buttons = self.checkbox_layout.count()
        extra_btns = abs(new_n_btns - old_n_buttons)
        # Add/Delete the extra buttons if there are extras
        if extra_btns:
            if new_n_btns > old_n_buttons:
                columns_limit = 4
                current_y = (old_n_buttons-1)//columns_limit
                current_x = (old_n_buttons-1)%columns_limit
                for n in range(old_n_buttons,new_n_btns):
                    current_x +=1
                    if current_x%columns_limit == 0:
                        current_y +=1
                    current_x = current_x%columns_limit
                    
                    chan_btn = QCheckBox('Channel %i' % n,self.channels_box)
                    chan_btn.setCheckState(Qt.Checked)
                    self.checkbox_layout.addWidget(chan_btn,current_y,current_x)
                    self.chan_btn_group.addButton(chan_btn,n)
            else:
                for n in range(old_n_buttons-1,self.rec.new_n_btns-1,-1):
                    chan_btn = self.chan_btn_group.button(n)
                    self.checkbox_layout.removeWidget(chan_btn)
                    self.chan_btn_group.removeButton(chan_btn)
                    chan_btn.deleteLater()
                
    def chan_line_toggle(self,chan_list):
        """
        Callback to intepret the input expressions and toggle the channels
        accordingly
        
        Parameters
        ----------
        chan_list: List of str
            Input expressions
        """
        # intepret the string into either int or range, then append/extend the all_selected_chan list
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
                    all_selected_chan.extend(range(int(r_in[0]),int(r_in[1])+1))
                else:
                    if not r_in[2]:
                        r_in[2] = 1
                    all_selected_chan.extend(range(int(r_in[0]),int(r_in[1])+1,int(r_in[2])))

        # Toggle checkboxes based on the integers in the list
        print(all_selected_chan)
        if all_selected_chan:
            n_btns = self.checkbox_layout.count()
            self.toggle_all_checkboxes(Qt.Unchecked)
            for chan in set(all_selected_chan):
                if chan < n_btns:
                    self.chan_btn_group.button(chan).click()
                    
    def toggle_channel_plot(self, btn):
        """
        Callback when a checkbox is clicked. 
        Emits sigToggleChanged.
        
        Parameters
        ----------
        btn: QCheckBox
            button that is clicked on
        """
        chan_num = self.chan_btn_group.id(btn)
        if btn.isChecked():
            self.sigToggleChanged.emit(chan_num,True)
        else:
            self.sigToggleChanged.emit(chan_num,False)

#-----------------------CHANNEL CONFIGURATION WIDGET-------------------------         
class ChanConfigUI(BaseWidget):
    """
     A Channel Plots Configuration widget.
     Contains: 
     - ComboBox to switch channel plot info,
     - Spinboxes to set the offsets
     - Buttons to change the colour of a plot
     - Checkbox to hold a signal
     - Button to open a window to edit metadata
     
     Attributes
     ----------
     timeOffsetChanged: pyqtsignal
         Emits when a time domain offset is changed, 
         Sends out the channel num(int) and the x and y offsets(float,float)
     freqOffsetChanged: pyqtsignal
         Emits when a frequency domain offset is changed, 
         Sends out the channel num(int) and the x and y offsets(float,float)
     sigHoldChanged: pyqtsignal
         Emits when a state of holding the plot is changed, 
         Sends out the channel num(int) and the state(bool)
     colourReset: pyqtsignal
         Emits when a plot colour is reset, 
         Sends out the channel num(int)
     colourChanged: pyqtsignal
         Emits when a plot colour is changed, 
         Sends out the channel num(int) and the color(QColor)
     chans_num_box: QComboBox
         The widget to select the channel plot
     hold_tickbox: QCheckBox
         Toggles whether to hold the signal or not
     colbox:QPushButton
         Set the colour of the plot
     defcol_btn: QPushButton
         Reset the colour of the plot to the default colour
     meta_btn: QPushButton
         Opens the metadata editing window
     time_offset_config: List of SpinBox
         Sets the X and Y offsets of time domain plot
     fft_offset_config: List of SpinBox
         Sets the X and Y offsets of frequency domain plot
    """
    sigTimeOffsetChanged = pyqtSignal(int,float,float)
    sigFreqOffsetChanged = pyqtSignal(int,float,float)
    sigHoldChanged = pyqtSignal(int,int)
    sigColourReset = pyqtSignal(int)
    sigColourChanged = pyqtSignal(int,object)
    
    def initUI(self):
        """
        Reimplemented from BaseWidget.
        """
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
        
        for cbox in self.time_offset_config:
            cbox.sigValueChanging.connect(fct.partial(self.set_plot_offset,'Time'))
        for cbox in self.fft_offset_config:
            cbox.sigValueChanging.connect(fct.partial(self.set_plot_offset,'DFT'))
        
        self.hold_tickbox.stateChanged.connect(self.signal_hold)
        self.colbox.sigColorChanging.connect(lambda: self.set_plot_colour())
        self.defcol_btn.clicked.connect(lambda: self.set_plot_colour(True))
           
    def set_offset_step(self,cbox,step_val):
        """
        Sets the single step of a spinbox
        
        Parameters
        ----------
        cbox: SpinBox
            SpinBox to set
        step_val: float
            The new value of the single step
        """
        cbox.setSingleStep(step_val)
        
    def set_plot_offset(self,dtype):
        """
        Callback to set the offset.
        Emits sigTimeOffsetChanged or sigFreqOffsetChanged depending on dtype
        
        Parameters
        ----------
        dtype: str
            Either 'Time' of 'DFT' to indicate the time domain or frequency domain plot respectively
        """
        chan = self.chans_num_box.currentIndex()
        if dtype == 'Time':
            self.sigTimeOffsetChanged.emit(chan,self.time_offset_config[0].value(),self.time_offset_config[1].value())
        elif dtype == 'DFT':
            self.sigFreqOffsetChanged.emit(chan,self.fft_offset_config[0].value(),self.fft_offset_config[1].value())
       
    def signal_hold(self,state):
        """
        Callback to hold the plot.
        Emits sigHoldChanged
        
        Parameters
        ----------
        dtype: str
            Either 'Time' of 'DFT' to indicate the time domain or frequency domain plot respectively
        """
        chan = self.chans_num_box.currentIndex()
        self.sigHoldChanged.emit(chan,state)
        
    def set_colour_btn(self,col):
        """
        Set the colour of the colour button.
        
        Parameters
        ----------
        col: QColor
            Colour to set
        """
        self.colbox.setColor(col)
        
    def set_plot_colour(self,reset = False):
        """
        Set the colour of the colour button.
        Emits either sigColourReset or sigColourChanged
        
        Parameters
        ----------
        reset: Bool
            Whether to reset the colour or not
        """
        chan = self.chans_num_box.currentIndex()
        if reset:
            self.sigColourReset.emit(chan)
        else:
            col = self.colbox.color()   
            self.sigColourChanged.emit(chan,col)

#-----------------------DEVICE CONFIGURATION WIDGET-------------------------        
class DevConfigUI(BaseWidget):
    """
     A Channel Plots Configuration widget.
     Contains: 
     - Widgets to setup the recorder
     
     Attributes
     ----------
     configRecorder: pyqtsignal
         Emits the configuration of the recorder is set
     typebtngroup: QButtonGroup
         Contains the buttons to select source of audio stream
         Either SoundCard or NI
     config_button: QPushButton
         Confirm the settings and set up the new recorder
     rec: Recorder object
         Reference of the Recorder object
     configboxes: List of widgets
         Widgets for the configuration settings, in order:
         ['Source','Rate','Channels','Chunk Size','Number of Chunks']
         with type, respectively:
         [QComboBox, QLineEdit, QLineEdit, QLineEdit, QLineEdit]
    """
    configRecorder = pyqtSignal()
    
    def initUI(self):
        """
        Reimplemented from BaseWidget.
        """
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
        
        # Set up QbuttonGroup to manage the buttons' Signals
        self.typebtngroup = QButtonGroup(self)
        self.typebtngroup.addButton(pyaudio_button)
        self.typebtngroup.addButton(NI_button)
        
        config_form.addRow(self.typegroup)
        
        # Add the remaining settings
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
        
        # Add the confirm button
        self.config_button = QPushButton('Set Config', self)
        config_form.addRow(self.config_button)
                
        self.config_button.clicked.connect(self.configRecorder.emit)
        self.typebtngroup.buttonReleased.connect(self.display_sources)
        
    def set_recorder(self,recorder):
        """
        Set the recorder for reference
        
        Parameters
        ----------
        recorder: Recorder object
            The reference of the Recorder object
        """
        self.rec = recorder
        
    def config_setup(self):
        """
        Configure the inputs of the config_boxes
        
        Parameters
        ----------
        recorder: Recorder object
            The reference of the Recorder object
        """
        rb = self.typegroup.findChildren(QRadioButton)
        if type(self.rec) == mR.Recorder:
            rb[0].setChecked(True)
        elif type(self.rec) == NIR.Recorder:
            rb[1].setChecked(True)
            
        self.display_sources()
        
        info = [self.rec.rate,self.rec.channels,
                self.rec.chunk_size,self.rec.num_chunk]
        for cbox,i in zip(self.configboxes[1:],info):
            cbox.setText(str(i))
        
    def display_sources(self):
        """
        Display the available sources from the type of recorder
        Either SoundCard(myRecorder) or NI(NIRecorder)
        """
        # Check which type of recorder is selected
        rb = self.typegroup.findChildren(QRadioButton)
        if rb[0].isChecked():
            selR = mR.Recorder()
        elif rb[1].isChecked():
            selR = NIR.Recorder()
        else:
            return
        
        # Clear and fill the source configbox
        source_box = self.configboxes[0]
        source_box.clear()
        try:
            full_device_name = []
            # 'extras' are extra details of the devices
            names,extras =  selR.available_devices()
            for name,extra in zip(names,extras):
                if type(extra) == str:
                    full_device_name.append(name + ' - ' + extra)
                else:
                    full_device_name.append(name)
                    
            source_box.addItems(full_device_name)
        except Exception as e:
            print(e)
            source_box.addItems(selR.available_devices()[0])

        source_box.setCurrentText(self.rec.device_name)
        del selR
        
    def read_device_config(self):
        """
        Display the available sources from the type of recorder
        Either SoundCard(myRecorder) or NI(NIRecorder)
        
        Returns
        ----------
        recType: str
            Type of recorder
        configs: list
            The configurations ['Source','Rate','Channels','Chunk Size','Number of Chunks']
            with type, respectively:[str, int, int, int, int]
        """
        # TODO: Put in QValidators
        recType =  [rb.isChecked() for rb in self.typegroup.findChildren(QRadioButton)]
        configs = []
        for cbox in self.configboxes:
            if type(cbox) == QComboBox:
                configs.append(cbox.currentIndex())
            else:
                config_input = cbox.text().strip(' ')
                configs.append(int(float(config_input)))
                    
        print(recType,configs)
        return(recType, configs)

#-----------------------------STATUS WIDGET-------------------------------        
class StatusUI(BaseWidget):
    """
     A Status Bar widget.
     Contains: 
     - QStatusBar to display the stream status
     - Button to reset the splitters
     - Button to resume/pause the stream
     - Button to grab a snapshot of the stream
     
     Attributes
     ----------
     statusbar: QStatusBar
         Displays the status of the stream
     resetView: QPushButton
         Reset the splitter view
     togglebtn: Recorder object
         Resume/pause the stream
     sshotbtn: List of widgets
         Grab a snapshot of the stream
    """
    def initUI(self):
        """
        Reimplemented from BaseWidget.
        """
        stps_layout = QHBoxLayout(self)
        
        self.statusbar = QStatusBar(self)
        self.statusbar.showMessage('streaming')
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
        
    def trigger_message(self):
        """
        Display a message when the recording trigger is set off
        """
        self.statusbar.showMessage('Triggered! Recording...')

#-----------------------------RECORDING WIDGET-------------------------------                
class RecUI(BaseWidget):
    """
    A Recording Configuration widget.
    Contains: 
    - ComboBox to change recording mode,
    - Widgets for setting up the recording:
        Recording samples/ duration
        Triggering
    - Additional widgets for specific recording mode:
        Normal: None
        Average transfer function: Buttons to undo or clear past autospectrum and crossspectrum
    
    Attributes
    ----------
    startRecording: pyqtsignal
        Emits when record button is pressed
    cancelRecording: pyqtsignal
        Emits when cancel button is pressed
    undoLastTfAvg: pyqtsignal
        Emits when undo last transfer function button is pressed
    clearTfAvg: pyqtsignal
        Emits when clear past transfer functions button is pressed
    switch_rec_box: QComboBox
        Switch recording options
    rec_boxes: List of Widgets
        Configurations: ['Samples','Seconds','Pretrigger','Ref. Channel','Trig. Level'] 
        with types    : [QLineEdit, QLineEdit, QLineEdit, QComboBox, QLineEdit]
    spec_settings_widget:QStackedWidget
        Contains the additional settings 
    input_chan_box: QComboBox
        Additional settings to put input channel for average transfer function calculation 
    """
    startRecording = pyqtSignal()
    cancelRecording = pyqtSignal()
    
    undoLastTfAvg = pyqtSignal()
    clearTfAvg = pyqtSignal()
    
    def initUI(self):
        """
        Reimplemented from BaseWidget.        
        """
        rec_settings_layout = QVBoxLayout(self)
        global_settings_layout = QFormLayout()
        self.spec_settings_widget= QStackedWidget(self)
        
        rec_title = QLabel('Recording Settings', self)
        rec_title.setStyleSheet('''
                                font: 18pt;
                                ''')
        rec_settings_layout.addWidget(rec_title)
                
        rec_settings_layout.addLayout(global_settings_layout)
        rec_settings_layout.addWidget(self.spec_settings_widget)
        
        self.switch_rec_box = QComboBox(self)
        self.switch_rec_box.addItems(['Normal','TF Avg.','TF Grid','<something>'])
        self.switch_rec_box.currentIndexChanged.connect(self.spec_settings_widget.setCurrentIndex)
        global_settings_layout.addRow(QLabel('Mode',self),self.switch_rec_box)

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
                
            global_settings_layout.addRow(QLabel(c,self),cbox)
            self.rec_boxes.append(cbox) 
            
        # Connect the sample and time input check
        self.rec_boxes[0].editingFinished.connect(lambda: self.autoset_record_config('Samples'))
        self.rec_boxes[1].editingFinished.connect(lambda: self.autoset_record_config('Time'))
        self.rec_boxes[2].editingFinished.connect(lambda: set_input_limits(self.rec_boxes[2],-1,self.rec.chunk_size,int))
        self.rec_boxes[2].textEdited.connect(self.toggle_trigger)
        
        self.normal_rec = QWidget(self)
        normal_rec_layout = QVBoxLayout(self.normal_rec)
        normal_rec_layout.addWidget(QLabel('No Additional Options',self)) 
        self.spec_settings_widget.addWidget(self.normal_rec)
        
        # Widgets for average transfer function
        self.tfavg_rec = QWidget(self)
        tfavg_rec_layout = QVBoxLayout(self.tfavg_rec)
        tfavg_settings = QFormLayout(self.tfavg_rec)
        self.input_chan_box = QComboBox(self)
        tfavg_settings.addRow(QLabel('Input',self),self.input_chan_box)
        avg_layout = QHBoxLayout()
        #self.avg_input_box = QLineEdit(self)
        self.avg_count_box = QLabel('Count: 0',self)
        #avg_layout.addWidget(self.avg_input_box)
        avg_layout.addWidget(self.avg_count_box)
        tfavg_settings.addRow(QLabel('Averages',self),avg_layout)
        tfavg_rec_layout.addLayout(tfavg_settings)
        # Buttons for average transfer function
        tflog_btn_layout = QHBoxLayout()
        self.undo_log_btn = QPushButton('Undo Last',self)
        self.undo_log_btn.clicked.connect(self.undoLastTfAvg.emit)
        tflog_btn_layout.addWidget(self.undo_log_btn)
        self.clear_log_btn = QPushButton('Clear',self)
        self.clear_log_btn.clicked.connect(self.clearTfAvg.emit)
        tflog_btn_layout.addWidget(self.clear_log_btn)        
        tfavg_rec_layout.addLayout(tflog_btn_layout)
        
        self.spec_settings_widget.addWidget(self.tfavg_rec)
        
        # Widgets for average transfer function grid
        self.tfgrid_rec = QWidget(self)
        tfgrid_rec_layout = QVBoxLayout(self.tfgrid_rec)
        tfgrid_rec_layout.addWidget(QLabel('Nothing is here :(',self))
        self.spec_settings_widget.addWidget(self.tfgrid_rec)
        
        # Placeholder
        self.something_rec = QWidget(self)
        something_rec_layout = QVBoxLayout(self.something_rec)
        something_rec_layout.addWidget(QLabel('<something is here>',self))
        self.spec_settings_widget.addWidget(self.something_rec)
        
        # Add the record and cancel buttons
        rec_btn_layout = QHBoxLayout(self.normal_rec)
        self.recordbtn = QPushButton('Log',self)
        self.recordbtn.resize(self.recordbtn.sizeHint())
        self.recordbtn.clicked.connect(self.startRecording.emit)
        rec_btn_layout.addWidget(self.recordbtn)
        self.cancelbtn = QPushButton('Cancel',self)
        self.cancelbtn.resize(self.cancelbtn.sizeHint())
        self.cancelbtn.setDisabled(True)
        self.cancelbtn.clicked.connect(self.cancelRecording.emit)
        rec_btn_layout.addWidget(self.cancelbtn)
        rec_settings_layout.addLayout(rec_btn_layout)
        
    def set_recorder(self,recorder):
        """
        Set the recorder reference
        """
        self.rec = recorder
        self.reset_configs()
        self.autoset_record_config('Time')
        if self.rec.channels <2:
            self.tfavg_rec.setDisabled(True)
        else:
            self.tfavg_rec.setEnabled(True)
            self.input_chan_box.clear()
            self.input_chan_box.addItems([str(i) for i in range(self.rec.channels)])
        
    def get_recording_mode(self):
        """
        Returns
        ----------
        str
            Current text of switch_rec_box 
        """
        return self.switch_rec_box.currentText()
    
    def get_input_channel(self):
        """
        Returns
        ----------
        int
            Current index of input_chan_box 
        """
        return self.input_chan_box.currentIndex()
    
    def get_record_config(self, *arg):
        """
        Returns
        ----------
        rec_configs: list
            List of recording settings
        """
        try:
            rec_configs = []
            data_type = [int,float,int,int,float]
            for cbox,dt in zip(self.rec_boxes,data_type):
                if type(cbox) == QComboBox:
                    #configs.append(cbox.currentText())
                    rec_configs.append(cbox.currentIndex())
                else:
                    config_input = cbox.text().strip(' ')
                    rec_configs.append(dt(float(config_input)))
            return(rec_configs)
        except Exception as e:
            print(e)
            return None
    
    def autoset_record_config(self, setting):
        """
        Recalculate samples or duration
        Parameter
        ----------
        setting: str
            Input type. Either 'Time' or 'Samples'
        """
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
        
    def reset_configs(self):
        """
        Reset the channels for triggering and reset validators
        """
        self.rec_boxes[3].clear()
        self.rec_boxes[3].addItems([str(i) for i in range(self.rec.channels)])
    
        validators = [QDoubleValidator(0.1,MAX_SAMPLE*self.rec.rate,1),
                     QIntValidator(-1,self.rec.chunk_size)]
        for cbox,vd in zip(self.rec_boxes[1:-2],validators):
            cbox.setValidator(vd)
            
    def update_TFavg_count(self,val):
        """
        Update the value of the number of recordings for average transfer function
        """
        self.avg_count_box.setText('Count: %i' % val)
        
    def toggle_trigger(self,string):
        """
        Enable or disable the trigger settings
        """
        try:
            val = int(string)
        except:
            val = -1
        
        if val == -1:
            self.rec_boxes[3].setEnabled(False)
            self.rec_boxes[4].setEnabled(False)
        else:
            self.rec_boxes[3].setEnabled(True)
            self.rec_boxes[4].setEnabled(True)
            
#-----------------------------????????------------------------------        
class ChanLineText(QLineEdit):
    returnPressed = pyqtSignal(list)
    
    def __init__(self,*arg,**kwarg):
        super().__init__(*arg,**kwarg)
        
        self.invalidchar_re = re.compile(r'[^\d,:]+')
        
    def keyPressEvent(self,event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            # REGEX here
            string = self.text()
            true_string = re.sub(self.invalidchar_re,'',string)
            self.setText(true_string)
            true_input = true_string.split(',')
                    
            self.returnPressed.emit(true_input)
            
        else:
            QLineEdit.keyPressEvent(self,  event)
            
def set_input_limits(linebox,low,high,in_type):
    val = in_type(linebox.text())
    linebox.setText( str(min(max(val,low),high)) )
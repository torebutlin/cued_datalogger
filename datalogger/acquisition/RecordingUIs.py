# -*- coding: utf-8 -*-
"""
Created on Tue Aug 22 11:19:29 2017

@author: eyt21
"""
from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QMainWindow,
    QPushButton, QDesktopWidget,QStatusBar, QLabel,QLineEdit, QFormLayout,
    QGroupBox,QRadioButton,QSplitter,QFrame, QComboBox,QScrollArea,QGridLayout,
    QCheckBox,QButtonGroup,QTextEdit,QApplication,QStackedWidget)
from PyQt5.QtGui import (QValidator,QIntValidator,QDoubleValidator,QColor,
QPalette,QPainter)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint
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
    toggleChanged = pyqtSignal(QPushButton)
    lineToggled = pyqtSignal(list)
    
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
        
        self.chan_btn_group.buttonClicked.connect(self.toggleChanged.emit)
        self.chan_text.returnPressed.connect(self.lineToggled.emit)
        
    def invert_checkboxes(self):
        for btn in self.channels_box.findChildren(QCheckBox):
            btn.click()
         
    def toggle_all_checkboxes(self,state):
        for btn in self.channels_box.findChildren(QCheckBox):
            if not btn.checkState() == state:
                btn.click()
        
class ChanConfigUI(BaseWidget):
    timeOffsetChanged = pyqtSignal(int,float,float)
    freqOffsetChanged = pyqtSignal(int,float,float)
    
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
        
        for cbox in self.time_offset_config:
            cbox.sigValueChanging.connect(fct.partial(self.set_plot_offset,'Time'))
        for cbox in self.fft_offset_config:
            cbox.sigValueChanging.connect(fct.partial(self.set_plot_offset,'DFT'))
           
    def set_offset_step(self,cbox,num):
        cbox.setSingleStep(num)
        
    def set_plot_offset(self,dtype):
        chan = self.chans_num_box.currentIndex()
        if dtype == 'Time':
            self.timeOffsetChanged.emit(chan,self.time_offset_config[0].value(),self.time_offset_config[1].value())
        elif dtype == 'DFT':
            self.freqOffsetChanged.emit(chan,self.fft_offset_config[0].value(),self.fft_offset_config[1].value())
            
class DevConfigUI(BaseWidget):
    recorderSelected = pyqtSignal()
    configRecorder = pyqtSignal()
    
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
                
        self.config_button.clicked.connect(self.configRecorder.emit)
        self.typebtngroup.buttonReleased.connect(self.display_sources)
        
    def set_recorder(self,recorder):
        self.rec = recorder
        
    def config_setup(self):
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
        # TODO: Put in Validators
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
    startRecording = pyqtSignal()
    cancelRecording = pyqtSignal()
    
    undoLastTfAvg = pyqtSignal()
    clearTfAvg = pyqtSignal()
    
    def initUI(self):
        
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
        
        tflog_btn_layout = QHBoxLayout()
        self.undo_log_btn = QPushButton('Undo Last',self)
        self.undo_log_btn.clicked.connect(self.undoLastTfAvg.emit)
        tflog_btn_layout.addWidget(self.undo_log_btn)
        self.clear_log_btn = QPushButton('Clear',self)
        self.clear_log_btn.clicked.connect(self.clearTfAvg.emit)
        tflog_btn_layout.addWidget(self.clear_log_btn)        
        tfavg_rec_layout.addLayout(tflog_btn_layout)
        
        self.spec_settings_widget.addWidget(self.tfavg_rec)
        
        self.tfgrid_rec = QWidget(self)
        tfgrid_rec_layout = QVBoxLayout(self.tfgrid_rec)
        tfgrid_rec_layout.addWidget(QLabel('Nothing is here :(',self))
        self.spec_settings_widget.addWidget(self.tfgrid_rec)
        
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
        return self.switch_rec_box.currentText()
    
    def get_input_channel(self):
        return self.input_chan_box.currentIndex()
    
    # Read the recording setting inputs
    def get_record_config(self, *arg):
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
            print(rec_configs)
            return(rec_configs)
        except Exception as e:
            print(e)
            return False
    
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
        
    def reset_configs(self):
        self.rec_boxes[3].clear()
        self.rec_boxes[3].addItems([str(i) for i in range(self.rec.channels)])
    
        validators = [QDoubleValidator(0.1,MAX_SAMPLE*self.rec.rate,1),
                     QIntValidator(-1,self.rec.chunk_size)]
        for cbox,vd in zip(self.rec_boxes[1:-2],validators):
            cbox.setValidator(vd)
            
    def update_TFavg_count(self,val):
        self.avg_count_box.setText('Count: %i' % val)
        
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
    print(val)
    linebox.setText( str(min(max(val,low),high)) )
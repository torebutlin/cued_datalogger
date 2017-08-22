# -*- coding: utf-8 -*-
"""
Created on Tue Aug 22 11:19:29 2017

@author: eyt21
"""
from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QMainWindow,
    QPushButton, QDesktopWidget,QStatusBar, QLabel,QLineEdit, QFormLayout,
    QGroupBox,QRadioButton,QSplitter,QFrame, QComboBox,QScrollArea,QGridLayout,
    QCheckBox,QButtonGroup,QTextEdit,QApplication,QStackedLayout)
from PyQt5.QtGui import (QValidator,QIntValidator,QDoubleValidator,QColor,
QPalette,QPainter)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt5.Qt import QStyleOption,QStyle

import re
import pyqtgraph as pg
import functools as fct

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
    lineToggled = pyqtSignal(str)
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
        
        self.chan_btn_group.buttonClicked.connect(self.emit_toggleChanged)
        self.chan_text.returnPressed.connect(self.emit_lineToggled)
        
    def invert_checkboxes(self):
        for btn in self.channels_box.findChildren(QCheckBox):
            btn.click()
         
    def toggle_all_checkboxes(self,state):
        for btn in self.channels_box.findChildren(QCheckBox):
            if not btn.checkState() == state:
                btn.click()
                
    def emit_toggleChanged(self,btn):
        self.toggleChanged.emit(btn)
        
    def emit_lineToggled(self,string):
        self.lineToggled.emit(string)

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
                
        self.config_button.clicked.connect(self.emit_configRecorder)
        self.typebtngroup.buttonReleased.connect(self.emit_recorderSelected)

    def emit_configRecorder(self):
        self.configRecorder.emit()
        
    def emit_recorderSelected(self):
        self.recorderSelected.emit()
        
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
    def initUI(self):
        rec_settings_layout = QVBoxLayout(self)
        global_settings_layout = QFormLayout()
        spec_settings_layout = QStackedLayout()
        
        rec_title = QLabel('Recording Settings', self)
        rec_title.setStyleSheet('''
                                font: 18pt;
                                ''')
        rec_settings_layout.addWidget(rec_title)
                
        rec_settings_layout.addLayout(global_settings_layout)
        rec_settings_layout.addLayout(spec_settings_layout)
        
        self.switch_rec_box = QComboBox(self)
        self.switch_rec_box.addItems(['Normal','TF Avg.','TF Grid','<something>'])
        self.switch_rec_box.currentIndexChanged.connect(spec_settings_layout.setCurrentIndex)
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
        
        self.normal_rec = QWidget(self)
        normal_rec_layout = QVBoxLayout(self.normal_rec)
        normal_rec_layout.addWidget(QLabel('No Additional Options',self)) 
        spec_settings_layout.addWidget(self.normal_rec)
        
        self.tfavg_rec = QWidget(self)
        tfavg_rec_layout = QVBoxLayout(self.tfavg_rec)
        tfavg_settings = QFormLayout(self.tfavg_rec)
        self.input_chan_box = QComboBox(self)
        self.input_chan_box.addItems([str(i) for i in range(3)])
        tfavg_settings.addRow(QLabel('Input',self),self.input_chan_box)
        self.avg_input_box = QLineEdit(self)
        tfavg_settings.addRow(QLabel('Averages',self),self.avg_input_box)
        tfavg_rec_layout.addLayout(tfavg_settings)
        
        tflog_btn_layout = QHBoxLayout()
        self.undo_log_btn = QPushButton('Undo Last',self)
        tflog_btn_layout.addWidget(self.undo_log_btn)
        self.clear_log_btn = QPushButton('Clear',self)
        tflog_btn_layout.addWidget(self.clear_log_btn)        
        tfavg_rec_layout.addLayout(tflog_btn_layout)
        
        spec_settings_layout.addWidget(self.tfavg_rec)
        
        self.tfgrid_rec = QWidget(self)
        tfgrid_rec_layout = QVBoxLayout(self.tfgrid_rec)
        tfgrid_rec_layout.addWidget(QLabel('Nothing is here :(',self))
        spec_settings_layout.addWidget(self.tfgrid_rec)
        
        self.something_rec = QWidget(self)
        something_rec_layout = QVBoxLayout(self.something_rec)
        something_rec_layout.addWidget(QLabel('<something is here>',self))
        spec_settings_layout.addWidget(self.something_rec)
        
        # Add the record and cancel buttons
        rec_btn_layout = QHBoxLayout(self.normal_rec)
        self.recordbtn = QPushButton('Log',self)
        self.recordbtn.resize(self.recordbtn.sizeHint())
        self.recordbtn.clicked.connect(self.emit_startRecording)
        rec_btn_layout.addWidget(self.recordbtn)
        self.cancelbtn = QPushButton('Cancel',self)
        self.cancelbtn.resize(self.cancelbtn.sizeHint())
        self.cancelbtn.setDisabled(True)
        self.recordbtn.clicked.connect(self.emit_cancelRecording)
        rec_btn_layout.addWidget(self.cancelbtn)
        rec_settings_layout.addLayout(rec_btn_layout)
        
        def emit_startRecording(self):
            self.startRecording.emit()
            
        def emit_cancelRecording(self):
            self.cancelRecording.emit()
        
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
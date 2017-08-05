# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 16:24:57 2017

@author: eyt21
"""
import sys
from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QMainWindow,
    QPushButton, QDesktopWidget,QStatusBar, QLabel,QLineEdit, QFormLayout,
    QGroupBox,QRadioButton,QSplitter,QFrame, QComboBox,QScrollArea,QGridLayout,
    QCheckBox,QButtonGroup,QTextEdit,QApplication,QListWidget,QDialog)
from PyQt5.QtGui import QValidator,QIntValidator,QDoubleValidator,QColor,QPalette,QSizePolicy
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint


class ChanMetaWin(QDialog):
    def __init__(self,livewin = None):
        super().__init__()
        
        self.livewin = livewin
        
        self.setGeometry(200,500,500,500)
        self.setWindowTitle('Channels Info')
        self.setModal(True)
        
        self.initUI()
        self.setFocus()
        self.show()
        
    def initUI(self):
        main_layout = QHBoxLayout(self)
        
        self.channel_listview = QListWidget(self)
        self.channel_listview.itemSelectionChanged.connect(self.display_metadata)

        self.all_info = self.livewin.live_chanset.chan_get_metadatas(
                ['name','cal_factor','units','tags','comments'])
        
        for i in range(len(self.all_info)):
            self.channel_listview.addItem(self.all_info[i]['name'])

        
        main_layout.addWidget(self.channel_listview)
        
        channel_meta_form = QGridLayout()
        
        title = QLabel('CHANNEL METADATA',self)
        title.setAlignment(Qt.AlignCenter)
        channel_meta_form.addWidget(title,0,0,1,3)
        meta_dtype = ('Channel','Name','Calibration Factor','Units','Tags','Comments')
        
        self.meta_configs = []
        UI_type = (QLabel,QLineEdit,QLineEdit,QLineEdit,QLineEdit,QTextEdit)
        def_inputs = [0] + list(self.all_info[0].values())
        row = 1
        for m,UI,d_in in zip(meta_dtype,UI_type,def_inputs):
            channel_meta_form.addWidget(QLabel(m,self),row,0,1,1)
            cbox = UI(str(d_in).strip('[]'),self)
            channel_meta_form.addWidget(cbox,row,1,1,2)
            self.meta_configs.append(cbox)
            row +=1
        
        row +=5
        
        apply_btn = QPushButton('Apply',self)
        yes_btn = QPushButton('Ok',self)
        no_btn =  QPushButton('Cancel',self)
        no_btn.clicked.connect(self.closing)
        channel_meta_form.addWidget(apply_btn,row,0)
        channel_meta_form.addWidget(yes_btn,row,1)
        channel_meta_form.addWidget(no_btn,row,2)
        
        main_layout.addLayout(channel_meta_form)
        
    def display_metadata(self):
        sel_num = self.channel_listview.currentRow()
        meta_values = [sel_num] + list(self.all_info[sel_num].values())
        for cbox,v in zip(self.meta_configs,meta_values):
            cbox.setText(str(v).strip('[]'))
    
    def closing(self):
        self.done(0)
 
if __name__ == '__main__':
    app = 0 
    app = QApplication(sys.argv)
    w = ChanMetaWin()
    sys.exit(app.exec_())
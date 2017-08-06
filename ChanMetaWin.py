# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 16:24:57 2017

@author: eyt21
"""
import sys,traceback
from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QMainWindow,
    QPushButton, QDesktopWidget,QStatusBar, QLabel,QLineEdit, QFormLayout,
    QGroupBox,QRadioButton,QSplitter,QFrame, QComboBox,QScrollArea,QGridLayout,
    QCheckBox,QButtonGroup,QTextEdit,QApplication,QListWidget,QDialog,QListWidgetItem )
from PyQt5.QtGui import QValidator,QIntValidator,QDoubleValidator,QColor,QPalette,QSizePolicy
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint
import functools as fct

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
        meta_dname = ('Channel','Name','Calibration Factor','Units','Tags','Comments')
        meta_dtype = ('','name','cal_factor','units','tags','comments')
        
        self.meta_configs = []
        UI_type = (QLabel,QLineEdit,QLineEdit,QLineEdit,QLineEdit,CommentBox)
        
        row = 1
        for m,UI,md in zip(meta_dname,UI_type,meta_dtype):
            channel_meta_form.addWidget(QLabel(m,self),row,0,1,1)
            cbox = UI(self)
            if not UI == QLabel:
                cbox.editingFinished.connect(fct.partial(self.update_metadata,md,cbox))
            channel_meta_form.addWidget(cbox,row,1,1,2)
            self.meta_configs.append(cbox)
            row +=1
        self.channel_listview.setCurrentRow(0)
        row +=5
        
        apply_btn = QPushButton('Apply',self)
        yes_btn = QPushButton('Ok',self)
        yes_btn.clicked.connect(self.export_metadata)
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
            
    def update_metadata(self,meta_name,UI):
        chan_num = self.channel_listview.currentRow()
        string = UI.text()
        try:
            if meta_name == 'tags':
                string = string.split(' ')
            self.all_info[chan_num][meta_name] = string
            
            if meta_name == 'name':
                self.channel_listview.currentItem().setText(string)
        except:
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))
            
    def export_metadata(self):
        try:
            for i in range(len(self.all_info)):
                self.livewin.live_chanset.chan_set_metadatas(self.all_info[i],num = i)
        except:
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))
            
        self.closing()
        
    def closing(self):
        self.done(0)
        
        
class CommentBox(QTextEdit):
    editingFinished = pyqtSignal()
        
    def focusOutEvent(self,event):
        self.editingFinished.emit()
        QTextEdit.focusOutEvent(self,event)
        
    def text(self):
        return self.toPlainText()
 
if __name__ == '__main__':
    app = 0 
    app = QApplication(sys.argv)
    w = ChanMetaWin()
    sys.exit(app.exec_())
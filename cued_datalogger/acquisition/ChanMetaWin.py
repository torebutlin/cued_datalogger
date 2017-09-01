# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 16:24:57 2017

@author: eyt21

This module contains the widget to open the window to edit metadata
in the acqusition window
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
    """
    This is the Modal Dialog Window to edit metadata from acquisition window.
    it shows the channel names on the left in a list, and the metadata on the right.
    
    Attributes
    ----------
    livewin: acquisition window
        Window to get the metadata from
    all_info: list
        Contains metadata for each channel
    channel_listview: QListWidget
        Display list of names of channels
    meta_configs: list
        Widget for ('Channel', 'Name', 'Calibration Factor', 'Tags', 'Comments')
        of types   (QLabel, QLineEdit, QLineEdit, QLineEdit, CommentBox)
    """
    def __init__(self,livewin = None):
        """
        Parameters
        ----------
        livewin: acquisition window
            Window to get the metadata from
        """
        super().__init__()
        
        self.livewin = livewin
        
        self.setGeometry(200,500,500,500)
        self.setWindowTitle('Channels Info')
        self.setModal(True)
        
        self.initUI()
        self.setFocus()
        self.show()
        
    def initUI(self):
        """
        Initialise the UI
        """
        main_layout = QHBoxLayout(self)
        
        self.channel_listview = QListWidget(self)
        self.channel_listview.itemSelectionChanged.connect(self.display_metadata)

        self.all_info = []
        for i in range(len(self.livewin.live_chanset)):
                self.all_info.append(self.livewin.live_chanset.get_channel_metadata(i))
        
        for i in range(len(self.all_info)):
            self.channel_listview.addItem(self.all_info[i]['name'])

        
        main_layout.addWidget(self.channel_listview)
        
        channel_meta_form = QGridLayout()
        
        title = QLabel('CHANNEL METADATA',self)
        title.setAlignment(Qt.AlignCenter)
        channel_meta_form.addWidget(title,0,0,1,3)
        meta_dname = ('Channel','Name','Calibration Factor','Tags','Comments')
        meta_dtype = ('','name','calibration_factor','tags','comments')
        
        self.meta_configs = []
        UI_type = (QLabel,QLineEdit,QLineEdit,QLineEdit,CommentBox)
        
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
        """
        Display the selected channel metadata
        """
        sel_num = self.channel_listview.currentRow()
        self.meta_configs[0].setText(str(sel_num))
        meta_dtype = ('name','calibration_factor','tags','comments')
        
        for n,md in enumerate(meta_dtype,1):
            self.meta_configs[n].setText(str(self.all_info[sel_num][md]))
            
    def update_metadata(self,meta_name,UI):
        """
        Update the selected channel metadata
        """
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
        """
        Export the metadata to the livewin ChannelSet
        """
        try:
            for i in range(len(self.all_info)):
                self.livewin.live_chanset.set_channel_metadata(i,self.all_info[i])
        except:
            t,v,tb = sys.exc_info()
            print(t)
            print(v)
            print(traceback.format_tb(tb))
            
        self.closing()
        
    def closing(self):
        self.done(0)
        
        
class CommentBox(QTextEdit):
    """
    Reimplement QTextEdit to be similar to QLineEdit,
    i.e. having editingFinished signal and text()
    """
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
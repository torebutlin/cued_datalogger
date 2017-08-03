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
        
        channel_listview = QListWidget(self)
        channel_listview.addItems(['Fruits','Apple','Stuff'])
        
        
        main_layout.addWidget(channel_listview)
        
        channel_meta_form = QGridLayout()
        
        title = QLabel('CHANNEL METADATA',self)
        title.setAlignment(Qt.AlignCenter)
        channel_meta_form.addWidget(title,0,0,1,3)
        meta_dtype = ('Channel','Name','Calibration Factor','Units','Tags','Comments')
        UI_type = (QLabel,QLineEdit,QLineEdit,QLineEdit,QLineEdit,QTextEdit)
        row = 1
        for m,UI in zip(meta_dtype,UI_type):
            channel_meta_form.addWidget(QLabel(m,self),row,0,1,1)
            channel_meta_form.addWidget(UI(self),row,1,1,2)
            row +=1
        
        row +=5
        
        apply_btn = QPushButton('Apply',self)
        yes_btn = QPushButton('Ok',self)
        no_btn =  QPushButton('Cancel',self)
        channel_meta_form.addWidget(apply_btn,row,0)
        channel_meta_form.addWidget(yes_btn,row,1)
        channel_meta_form.addWidget(no_btn,row,2)
        
        main_layout.addLayout(channel_meta_form)
'''  
if __name__ == '__main__':
    app = 0 
    app = QApplication(sys.argv)
    w = ChanMetaWin()
    sys.exit(app.exec_())'''
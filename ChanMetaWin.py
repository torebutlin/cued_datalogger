# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 16:24:57 2017

@author: eyt21
"""
import sys
from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QMainWindow,
    QPushButton, QDesktopWidget,QStatusBar, QLabel,QLineEdit, QFormLayout,
    QGroupBox,QRadioButton,QSplitter,QFrame, QComboBox,QScrollArea,QGridLayout,
    QCheckBox,QButtonGroup,QTextEdit,QApplication )
from PyQt5.QtGui import QValidator,QIntValidator,QDoubleValidator,QColor,QPalette,QSizePolicy
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint


class ChanMetaWin(QWidget):
    def __init__(self,livewin = None):
        super().__init__()
        
        self.livewin = livewin
        
        self.setGeometry(200,500,700,500)
        self.setWindowTitle('Channels Info')
        
        self.setFocus()
        self.show()
        
    def initUI(self):
        pass
        
    
if __name__ == '__main__':
    app = 0 
    app = QApplication(sys.argv)
    w = ChanMetaWin()
    sys.exit(app.exec_())
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 31 12:25:07 2017

@author: eyt21
"""
import sys,traceback
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import Qt,pyqtSignal
import re
 
class ChanLineText(QTextEdit):
    editingFinished = pyqtSignal()
        
    def keyPressEvent(self,event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.editingFinished.emit()
        else:
            QTextEdit.keyPressEvent(self,  event)
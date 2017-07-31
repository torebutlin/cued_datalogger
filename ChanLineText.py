# -*- coding: utf-8 -*-
"""
Created on Mon Jul 31 12:25:07 2017

@author: eyt21
"""

from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import Qt,pyqtSignal
import re
 
class ChanLineText(QTextEdit):
    validedit = pyqtSignal(list)
    
    def __init__(self,*arg,**kwarg):
        super().__init__(*arg,**kwarg)
        
        self.invalidchar_re = re.compile(r'[^\d\-,;]+')
        self.delimiter_re = re.compile(r'[,;]')
        
    def keyPressEvent(self,event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            # REGEX here
            string = self.toPlainText()
            true_string = re.sub(self.invalidchar_re,'',string)
            self.setText(true_string)
            true_input = re.split(self.delimiter_re,true_string)
            self.validedit.emit(true_input)
            
        else:
            QTextEdit.keyPressEvent(self,  event)
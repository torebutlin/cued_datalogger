# -*- coding: utf-8 -*-
"""
Created on Wed Jul 19 11:28:37 2017

@author: eyt21

PyQt signals for the Recorder Classes
"""

from PyQt5.QtCore import QObject, pyqtSignal

class RecEmitter(QObject):
    """
    PyQt signals for the Recorder Classes
    
    Attributes
    ----------
    recorddone: pyqtsignal
        Emits when recording is done
    triggered: pyqtsignal
        Emits when trigger threshold is reached
    newdata: pyqtsignal
        Emits when new data is received (not used)
    """
    recorddone = pyqtSignal()
    triggered = pyqtSignal()
    newdata = pyqtSignal()
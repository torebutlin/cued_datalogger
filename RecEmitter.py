# -*- coding: utf-8 -*-
"""
Created on Wed Jul 19 11:28:37 2017

@author: eyt21
"""
from PyQt5.QtCore import QObject, pyqtSignal

class RecEmitter(QObject):
    recorddone = pyqtSignal()
    triggered = pyqtSignal()
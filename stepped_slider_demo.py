import sys
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import (QWidget, QLCDNumber, QSlider, QSpinBox,QHBoxLayout,
    QVBoxLayout, QApplication)

import numpy as np

from mypyqt_widgets import Power2SteppedSlider, Power2SteppedSpinBox
       

class Example(QWidget):
    
    def __init__(self):
        super().__init__()
        
        self.initUI()
        
        
    def initUI(self):
        lcd = QLCDNumber(self)
        sld = Power2SteppedSlider(Qt.Horizontal, self)
        sp = Power2SteppedSpinBox(self)
        
        sp.setRange(32, 1024)
        sld.setRange(32, 1024)
    
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(sp)
        hbox.addWidget(sld)        
        vbox.addWidget(lcd)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        
        sp.valueChanged.connect(sld.setValue)
        sld.valueChanged.connect(sp.setValue)
        
        sp.valueChanged.connect(lcd.display)
        sld.valueChanged.connect(lcd.display)


        sp.setValue(256)
        
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Signal & slot')
        self.show()
        

if __name__ == '__main__':
    app=0
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())# -*- coding: utf-8 -*-


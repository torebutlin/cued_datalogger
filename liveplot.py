# -*- coding: utf-8 -*-
"""
Created on Wed Jul  5 13:12:34 2017

@author: eyt21
"""
import sys
from PyQt5.QtWidgets import (QWidget, QToolTip,QVBoxLayout,
    QPushButton, QApplication, QMessageBox, QDesktopWidget,QSizePolicy)
from PyQt5.QtGui import QIcon,QFont
from PyQt5.QtCore import QCoreApplication,QTimer

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation

from Recorder import *

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        self.compute_initial_figure()

        #
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass

class Example(QWidget):
    def __init__(self):
        super().__init__()
        
        self.initUI()
        
    def initUI(self):
        
        QToolTip.setFont(QFont('SansSerif', 10))
        self.setGeometry(500,500,500,500)
        self.setWindowTitle('LiveStreamPlot')
        self.setWindowIcon(QIcon('purewave.jpg'))
        
        vbox = QVBoxLayout()
        self.canvas = MyMplCanvas(self, width=5, height=4, dpi=100)
        vbox.addWidget(self.canvas)
        
        self.btn = QPushButton('Switch',self)
        self.btn.resize(self.btn.sizeHint())
        self.btn.pressed.connect(self.modify_rec)
        vbox.addWidget(self.btn)
        
        self.rec = Recorder(1,44100,1024,'Line (U24XL with SPDIF I/O)')
        self.rec.stream_init(playback = True)
        self.playing = True
        
        self.canvas.axes.set_ylim(-5e4,5e4)
        self.line, = self.canvas.axes.plot(
                range(len(self.rec.signal_data)),self.rec.signal_data)
        
        timer = QTimer(self)
        timer.timeout.connect(self.update_line)
        timer.start(0.1)
        
        
        self.center()
        self.show()
        
    def update_line(self):
        self.line.set_ydata(self.rec.signal_data)
        self.canvas.draw()
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def modify_rec(self):
        if self.playing:
            self.rec.stream_stop()
            self.playing = False
        else:
            self.rec.stream_init(playback = True)
            self.playing = True
        
    def closeEvent(self,event):
        reply = QMessageBox.question(self,'Message',
        'Are you sure you want to quit?', QMessageBox.Yes|
        QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.rec.stream_stop()
            event.accept()
        else:
            event.ignore()
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Example()
    sys.exit(app.exec_())
 
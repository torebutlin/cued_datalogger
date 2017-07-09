# -*- coding: utf-8 -*-
"""
Created on Wed Jul  5 13:12:34 2017

@author: eyt21
"""
import sys
from PyQt5.QtWidgets import (QWidget, QToolTip,QVBoxLayout,QMainWindow,
    QPushButton, QApplication, QMessageBox, QDesktopWidget,QSizePolicy)
#from PyQt5.QtGui import QIcon,QFont
from PyQt5.QtCore import QCoreApplication,QTimer

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
#import numpy as np

import myRecorder as rcd

#--------------------- Canvas Widget Class------------------------------------
class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        self.compute_initial_figure()
        
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass
#--------------------- The App Class------------------------------------
class Example(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set window parameter
        self.setGeometry(500,500,500,500)
        self.setWindowTitle('LiveStreamPlot')
        
        # Set recorder object
        self.rec = rcd.Recorder(device_name = 'Line (U24XL with SPDIF I/O)')
        self.rec.stream_init(playback = True)
        self.playing = True
        
        # Construct UI        
        self.initUI()
        
        # Center and show window
        self.center()
        self.setFocus()
        self.show()
     #------------- App construction methods--------------------------------     
    def initUI(self):
        # Setup the plot canvas        
        self.main_widget = QWidget(self)
        vbox = QVBoxLayout(self.main_widget)
        self.canvas = MyMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        vbox.addWidget(self.canvas)
        self.canvas.axes.set_ylim(-5e4,5e4)
        self.line, = self.canvas.axes.plot(
                range(len(self.rec.get_buffer())),self.rec.get_buffer())
        
        # Set up the button
        btn = QPushButton('Switch',self.main_widget)
        btn.resize(btn.sizeHint())
        btn.pressed.connect(self.toggle_rec)
        vbox.addWidget(btn)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        
        # Set up a timer to update the plot
        timer = QTimer(self)
        timer.timeout.connect(self.update_line)
        timer.start(0.1)
    
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    #------------- UI callback methods--------------------------------       
    def toggle_rec(self):
        if self.playing:
            self.rec.stream_stop()
        else:
            self.rec.stream_start()
        self.playing = not self.playing
        
    def update_line(self):
        self.line.set_ydata(self.rec.get_buffer())
        self.canvas.draw()
        
    #----------------Overrding methods------------------------------------
    # The method to call when the mainWindow is being close       
    def closeEvent(self,event):
        reply = QMessageBox.question(self,'Message',
        'Are you sure you want to quit?', QMessageBox.Yes|
        QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.rec.close()
            event.accept()
        else:
            event.ignore()
            
#----------------Main loop------------------------------------         
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Example()
    sys.exit(app.exec_())
 
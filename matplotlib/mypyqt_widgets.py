from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QSlider, QSpinBox

import numpy as np


class Power2SteppedSlider(QSlider):
    
    valueChanged = pyqtSignal(int)
      
    def __init__(self, orientation, parent=None):

        QSlider.__init__(self, orientation)
        
        # Update value whenever slider is moved
        self.sliderMoved.connect(self.round_to_power_2)
            
    def round_to_power_2(self, value):
        # Round value to nearest power of 2
        n = np.round(np.log(value)/np.log(2))
        self.setValue(2**n)
        self.valueChanged.emit(2**n)
        
        
class Power2SteppedSpinBox(QSpinBox):
    
    valueChanged = pyqtSignal(int)
     
    def __init__(self, parent=None):

        QSpinBox.__init__(self)
        
        # Update data when focus is lost or enter pressed
        self.editingFinished.connect(self.round_to_power_2)
        
        # Lose focus if clicked elsewhere
        self.setFocusPolicy(Qt.ClickFocus)
        parent.setFocusPolicy(Qt.ClickFocus)
               
    def round_to_power_2(self):
        # Round value to nearest power of 2
        n = np.round(np.log(self.value())/np.log(2))
        self.setValue(2**n)
        self.valueChanged.emit(2**n)
    
    def mouseReleaseEvent(self, event):
        # Lose focus if mouse released
        self.clearFocus()

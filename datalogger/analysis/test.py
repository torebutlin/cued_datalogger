import sys

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QTableWidget,
                             QDoubleSpinBox, QCheckBox, QPushButton, QGroupBox,
                             QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QFileDialog, QTreeWidget, QTreeWidgetItem, QTreeView,
                             QSpinBox, QRadioButton)

class CircleFitResults(QGroupBox):
    """
    The tree of results for the Circle Fit.
    
    Attributes
    ----------
    sig_selected_peak_changed : pyqtSignal(int)
        The signal emitted when the selected peak is changed.
    """
    
    sig_selected_peak_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__("Results", parent)
        
        self.num_channels = 4
        self.num_peaks = 0
                
        self.init_ui()
    
    def init_ui(self):       
        # # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Frequency", "Damping ratio",
                                   "Amplitude", "Phase", "Select"])
        
        # # Controls
        self.add_peak_btn = QPushButton("Add new peak", self)
        self.add_peak_btn.clicked.connect(self.add_peak)

        self.delete_selected_btn = QPushButton("Delete selected", self)
        self.delete_selected_btn.clicked.connect(self.delete_selected)
        
        controls = QGridLayout()
        controls.addWidget(self.add_peak_btn, 0, 0)
        controls.setColumnStretch(1, 1)
        controls.addWidget(self.delete_selected_btn, 0, 2)
        
        # # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        layout.addLayout(controls)
        
        self.setLayout(layout)
    
    def add_peak(self):
        """Add a new peak to the tree, with children for each channel."""
        # Create the parent item for the peak
        peak_item = QTreeWidgetItem(self.tree, 
                                    ["Peak {}".format(self.num_peaks), 
                                     "", "", "", "", ""])
        # Put a radio button in column 5
        radio_btn = QRadioButton()
        radio_btn.toggled.connect(self.on_selected_peak_changed)
        self.tree.setItemWidget(peak_item, 5, radio_btn)
        
        # Put spinboxes in columns 1-4
        for col in [1,2,3,4]:        
            self.tree.setItemWidget(peak_item, col, QSpinBox())
        
        # Create the child items for each channel for this peak if there's
        # more than one channel
        if self.num_channels > 1:
            for i in range(self.num_channels):
                channel_item = QTreeWidgetItem(peak_item,
                                               ["Channel {}".format(i),
                                                "", "", "", "", ""])
                # Put spinboxes in cols 1-4
                for col in [1,2,3,4]:        
                    self.tree.setItemWidget(channel_item, col, QSpinBox())
        
        # Register that we've added another peak
        self.num_peaks += 1
    
    def delete_selected(self):
        """Delete the item that is currently selected."""
        for i in range(self.tree.topLevelItemCount()):
            # If the radio button is checked
            if self.tree.itemWidget(self.tree.topLevelItem(i), 5).isChecked():
                # Delete this item
                self.tree.takeTopLevelItem(i)
                #self.num_peaks -= 1
    
    def on_selected_peak_changed(self, checked):
        for i in range(self.tree.topLevelItemCount()):
            # If the radio button in this row is the sender
            if self.tree.itemWidget(self.tree.topLevelItem(i), 5) == self.sender():
                if checked:
                    print("Selected: " + str(i))
                    self.sig_selected_peak_changed.emit(i)
                else:
                    pass

    def update_parameter_values(self):
        pass
    
    def frequency(self, peak_number, channel_number=None):
        if channel_number is None:
            return self.tree.itemWidget(self.tree.topLevelItem(peak_number), 1).value()
            



app=0
app=QApplication(sys.argv)
w = CircleFitResults()
w.show()
sys.exit(app.exec_())           

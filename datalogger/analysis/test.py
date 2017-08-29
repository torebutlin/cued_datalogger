import sys
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QTableWidget,
                             QDoubleSpinBox, QPushButton, QGroupBox,
                             QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QTreeWidget, QTreeWidgetItem,
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
        
        # TODO
        self.num_channels = 4
        self.num_peaks = 0
                
        self.init_ui()
    
    def init_ui(self):       
        # # Tree for values
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Frequency", "Damping ratio",
                                   "Amplitude", "Phase", "Select"])
    
        # # Tree for autofit parameters
        self.autofit_tree = QTreeWidget()
        self.autofit_tree.setHeaderLabels(["Name", "Frequency", "Damping ratio",
                                           "Amplitude", "Phase", "Select"])
        
        # # Controls
        self.add_peak_btn = QPushButton("Add new peak", self)
        self.add_peak_btn.clicked.connect(self.add_peak)

        self.delete_selected_btn = QPushButton("Delete selected", self)
        self.delete_selected_btn.clicked.connect(self.delete_selected)
        
        self.set_autofit_btn = QPushButton("Set autofit parameters", self)
        self.set_autofit_btn.clicked.connect(self.set_autofit_parameters)
        
        controls = QGridLayout()
        controls.addWidget(self.add_peak_btn, 0, 0)
        controls.setColumnStretch(1, 1)
        controls.addWidget(self.delete_selected_btn, 0, 2)
        controls.addWidget(self.set_autofit_btn, 1, 2)
        
        # # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        layout.addLayout(controls)
        
        self.setLayout(layout)
    
    def add_peak(self):
        """Add a top-level item for a new peak to the tree, with children for
        each channel."""        
        # Create the parent item for the peak
        peak_item = QTreeWidgetItem(self.tree, 
                                    ["Peak {}".format(self.num_peaks), 
                                     "", "", "", "", ""])
        # Put a radio button in column 5 in the tree
        radio_btn = QRadioButton()
        radio_btn.toggled.connect(self.on_selected_peak_changed)
        self.tree.setItemWidget(peak_item, 5, radio_btn)
        
        for col in [1, 2, 3, 4]:
            # Put spinboxes in the tree
            spinbox = QDoubleSpinBox()
            self.tree.setItemWidget(peak_item, col, spinbox)
            # Put comboboxes in the autofit tree
            combobox = QComboBox()
            combobox.addItems(["Auto", "Manual"])
            self.autofit_tree.setItemWidget(peak_item, col, combobox)
        
        # Create the child items for each channel for this peak if there's
        # more than one channel
        if self.num_channels > 1:
            for i in range(self.num_channels):
                channel_item = QTreeWidgetItem(peak_item,
                                               ["Channel {}".format(i),
                                                "", "", "", "", ""])
                for col in [1, 2, 3, 4]:
                    # Put spinboxes in the tree
                    spinbox = QDoubleSpinBox()
                    spinbox.valueChanged.connect(self.update_peak_average)
                    self.tree.setItemWidget(channel_item, col, spinbox)
                    # Put comboboxes in the autofit tree
                    combobox = QComboBox()
                    combobox.addItems(["Auto", "Manual"])
                    self.autofit_tree.setItemWidget(channel_item, col, combobox)
        
        # Register that we've added another peak
        self.num_peaks += 1
    
    def delete_selected(self):
        """Delete the item that is currently selected."""
        for i in range(self.tree.topLevelItemCount()):
            # If the radio button is checked
            peak_item = self.tree.topLevelItem(i)
            if peak_item is not None:
                if self.tree.itemWidget(peak_item, 5).isChecked():
                    # Delete this item
                    self.tree.takeTopLevelItem(i)
                    #self.num_peaks -= 1
    
    def on_selected_peak_changed(self, checked):
        for i in range(self.tree.topLevelItemCount()):
            # If the radio button in this row is the sender
            peak_item = self.tree.topLevelItem(i)
            if peak_item is not None:
                if self.tree.itemWidget(peak_item, 5) == self.sender():
                    if checked:
                        print("Selected: " + str(i))
                        self.sig_selected_peak_changed.emit(i)
                    else:
                        pass

    def update_parameter_values(self):
        pass
    
    def update_peak_average(self):
        """Set the parameter values displayed for the peak to the average of 
        all the channel values for each parameter."""
        for peak_number in range(self.num_peaks):
            # Get the peak item
            peak_item = self.tree.topLevelItem(peak_number)

            if peak_item is not None:
                # Find the average values of all the channels
                avg_frequency = 0
                avg_damping = 0
                avg_amplitude = 0
                avg_phase = 0
                
                for channel_number in range(self.num_channels):
                    avg_frequency += self.get_frequency(peak_number, channel_number)
                    avg_damping += self.get_damping(peak_number, channel_number)
                    avg_amplitude += self.get_amplitude(peak_number, channel_number)
                    avg_phase += self.get_phase(peak_number, channel_number)
                
                avg_frequency /= self.num_channels
                avg_damping /= self.num_channels
                avg_amplitude /= self.num_channels
                avg_phase /= self.num_channels
                
                # Set the peak item to display the averages
                self.tree.itemWidget(peak_item, 1).setValue(avg_frequency)
                self.tree.itemWidget(peak_item, 2).setValue(avg_damping)
                self.tree.itemWidget(peak_item, 3).setValue(avg_amplitude)
                self.tree.itemWidget(peak_item, 4).setValue(avg_phase)
    
    def get_frequency(self, peak_number, channel_number=None):
        """Return the resonant frequency of the peak given by 
        *peak_number*. If *channel_number* is given, return the resonant  
        frequency of the given peak in the given channel."""
        peak_item = self.tree.topLevelItem(peak_number)
        if peak_item is not None:
            if channel_number is None:
                spinbox = self.tree.itemWidget(peak_item, 1)
                return spinbox.value()
            else:
                channel_item = peak_item.child(channel_number)
                spinbox = self.tree.itemWidget(channel_item, 1)
                return spinbox.value()
        else:
            return 0
       
    def get_damping(self, peak_number, channel_number=None):
        """Return the damping ratio of the peak given by *peak_number*. If 
        *channel_number* is given, return the damping ratio of the given peak
        in the given channel."""
        peak_item = self.tree.topLevelItem(peak_number)
        if peak_item is not None:
            if channel_number is None:
                spinbox = self.tree.itemWidget(peak_item, 2)
                return spinbox.value()
            else:
                channel_item = peak_item.child(channel_number)
                spinbox = self.tree.itemWidget(channel_item, 2)
                return spinbox.value()
        else:
            return 0     
       
    def get_amplitude(self, peak_number, channel_number=None):
        """Return the amplitude of the peak given by *peak_number*. If 
        *channel_number* is given, return the amplitude of the given peak in 
        the given channel."""
        peak_item = self.tree.topLevelItem(peak_number)
        if peak_item is not None:
            if channel_number is None:
                spinbox = self.tree.itemWidget(peak_item, 3)
                return spinbox.value()
            else:
                channel_item = peak_item.child(channel_number)
                spinbox = self.tree.itemWidget(channel_item, 3)
                return spinbox.value()
        else:
            return 0
       
    def get_phase(self, peak_number, channel_number=None):
        """Return the phase of the peak given by *peak_number*. If 
        *channel_number* is given, return the phase of the given peak in the
        given channel."""
        peak_item = self.tree.topLevelItem(peak_number)
        if peak_item is not None:
            if channel_number is None:
                spinbox = self.tree.itemWidget(peak_item, 4)
                return spinbox.value()
            else:
                channel_item = peak_item.child(channel_number)
                spinbox = self.tree.itemWidget(channel_item, 4)
                return spinbox.value()
        else:
            return 0


app=0
app=QApplication(sys.argv)
w = CircleFitResults()
w.show()
sys.exit(app.exec_())           

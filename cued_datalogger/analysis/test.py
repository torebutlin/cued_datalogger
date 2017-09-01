import sys
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QTableWidget,
                             QDoubleSpinBox, QPushButton, QGroupBox,
                             QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QTreeWidget, QTreeWidgetItem,
                             QSpinBox, QRadioButton)


class CircleFitTree(QGroupBox):
    """
    The tree displaying the Circle Fit results and the parameters used for
    automatically fitting the circle.

    Attributes
    ----------
    sig_selected_peak_changed : pyqtSignal(int)
        The signal emitted when the selected peak is changed.
    """

    sig_selected_peak_changed = pyqtSignal(int)

    def __init__(self, parent=None, channelset=None):
        super().__init__("Results", parent)

        # TODO
        if channelset is None:
            self.num_channels = 5
        else:
            self.num_channels = len(channelset)

        self.num_peaks = 0

        self.init_ui()

    def init_ui(self):
        # # Tree for values
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Frequency", "Damping ratio",
                                   "Amplitude", "Phase", "Select"])
        self.tree.setStyleSheet("QTreeWidget::item:has-children { background-color : palette(mid);}")

        # # Tree for autofit parameters
        self.autofit_tree = QTreeWidget()
        self.autofit_tree.setHeaderLabels(["Name", "Frequency", "Damping ratio",
                                           "Amplitude", "Phase", "Select"])
        self.autofit_tree.hide()
        self.autofit_tree.setStyleSheet("QTreeWidget::item:has-children { background-color : palette(mid);}")

        # Connect the two trees together, so the views look identical
        self.autofit_tree.itemCollapsed.connect(self.on_item_collapsed)
        self.autofit_tree.itemExpanded.connect(self.on_item_expanded)
        self.tree.itemCollapsed.connect(self.on_item_collapsed)
        self.tree.itemExpanded.connect(self.on_item_expanded)

        # # Controls
        self.add_peak_btn = QPushButton("Add new peak", self)
        self.add_peak_btn.clicked.connect(self.add_peak)

        self.delete_selected_btn = QPushButton("Delete selected", self)
        self.delete_selected_btn.clicked.connect(self.delete_selected)

        self.view_autofit_btn = QPushButton("View autofit parameters", self)
        self.view_autofit_btn.clicked.connect(self.toggle_view)

        self.reset_to_autofit_btn = QPushButton("Reset all to auto", self)
        self.reset_to_autofit_btn.clicked.connect(self.reset_to_autofit)
        self.reset_to_autofit_btn.hide()

        controls1 = QGridLayout()
        controls1.addWidget(self.add_peak_btn, 0, 0)
        controls1.setColumnStretch(1, 1)
        controls1.addWidget(self.delete_selected_btn, 0, 2)

        controls2 = QGridLayout()
        controls2.setColumnStretch(0, 1)
        controls2.addWidget(self.reset_to_autofit_btn, 0, 1)
        controls2.addWidget(self.view_autofit_btn, 0, 2)

        # # Layout
        layout = QGridLayout()
        layout.addLayout(controls2, 0, 0)
        layout.addWidget(self.tree, 1, 0)
        layout.addWidget(self.autofit_tree, 1, 0)
        layout.addLayout(controls1, 2, 0)

        self.setLayout(layout)

    def add_peak(self):
        """Add a top-level item for a new peak to the tree, with children for
        each channel."""
        # Create the parent item for the peak
        peak_item = QTreeWidgetItem(self.tree,
                                    ["Peak {}".format(self.num_peaks),
                                     "", "", "", "", ""])
        autofit_peak_item = QTreeWidgetItem(self.autofit_tree,
                                            ["Peak {}".format(self.num_peaks),
                                             "", "", "", "", ""])

        # Put a radio button in column 5 in the tree
        radio_btn = QRadioButton()
        radio_btn.toggled.connect(self.on_selected_peak_changed)
        self.tree.setItemWidget(peak_item, 5, radio_btn)
        radio_btn.setChecked(True)

        for col in [1, 2, 3, 4]:
            # Put spinboxes in the tree
            spinbox = QDoubleSpinBox()
            self.tree.setItemWidget(peak_item, col, spinbox)
            # Put comboboxes in the autofit tree
            combobox = QComboBox()
            combobox.addItems(["Auto", "Manual"])
            combobox.currentIndexChanged.connect(self.update_peak_average)
            self.autofit_tree.setItemWidget(autofit_peak_item, col, combobox)

        # Create the child items for each channel for this peak if there's
        # more than one channel
        if self.num_channels > 1:
            for i in range(self.num_channels):
                channel_item = QTreeWidgetItem(peak_item,
                                               ["Channel {}".format(i),
                                                "", "", "", "", ""])
                autofit_channel_item = QTreeWidgetItem(autofit_peak_item,
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
                    combobox.currentIndexChanged.connect(self.update_peak_average)
                    self.autofit_tree.setItemWidget(autofit_channel_item,
                                                    col, combobox)

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
                    self.autofit_tree.takeTopLevelItem(i)
                    #self.num_peaks -= 1

    def toggle_view(self):
        if self.tree.isVisible():
            self.tree.hide()
            self.autofit_tree.show()
            self.reset_to_autofit_btn.show()
            self.view_autofit_btn.setText("View parameter values")
        else:
            self.tree.show()
            self.autofit_tree.hide()
            self.reset_to_autofit_btn.hide()
            self.view_autofit_btn.setText("View autofit parameters")

    def on_item_collapsed(self, item):
        index = self.sender().indexOfTopLevelItem(item)
        self.tree.collapseItem(self.tree.topLevelItem(index))
        self.autofit_tree.collapseItem(self.autofit_tree.topLevelItem(index))

    def on_item_expanded(self, item):
        index = self.sender().indexOfTopLevelItem(item)
        self.tree.expandItem(self.tree.topLevelItem(index))
        self.autofit_tree.expandItem(self.autofit_tree.topLevelItem(index))

    def on_selected_peak_changed(self, checked):
        for i in range(self.tree.topLevelItemCount()):
            # If the radio button in this row is the sender
            peak_item = self.tree.topLevelItem(i)
            if peak_item is not None:
                if self.tree.itemWidget(peak_item, 5) == self.sender():
                    if checked:
                        print("Selected: " + str(i))
                        self.sig_selected_peak_changed.emit(i)

    def reset_to_autofit(self):
        """Reset all parameters to be automatically adjusted."""
        for peak_number in range(self.num_peaks):
            peak_item = self.autofit_tree.topLevelItem(peak_number)

            for col in [1, 2, 3, 4]:
                self.autofit_tree.itemWidget(peak_item, col).setCurrentIndex(0)

            if self.num_channels > 1:
                for channel_number in range(self.num_channels):
                    channel_item = peak_item.child(channel_number)
                    for col in [1, 2, 3, 4]:
                        self.autofit_tree.itemWidget(channel_item, col).setCurrentIndex(0)

    def update_peak_average(self):
        """Set the parameter values displayed for the peak to the average of
        all the channel values for each parameter."""
        for peak_number in range(self.num_peaks):
            # Get the peak item
            peak_item = self.tree.topLevelItem(peak_number)
            autofit_item = self.autofit_tree.topLevelItem(peak_number)

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
                if self.autofit_tree.itemWidget(autofit_item, 1).currentText() == "Auto":
                    self.tree.itemWidget(peak_item, 1).setValue(avg_frequency)
                if self.autofit_tree.itemWidget(autofit_item, 2).currentText() == "Auto":
                    self.tree.itemWidget(peak_item, 2).setValue(avg_damping)
                if self.autofit_tree.itemWidget(autofit_item, 3).currentText() == "Auto":
                    self.tree.itemWidget(peak_item, 3).setValue(avg_amplitude)
                if self.autofit_tree.itemWidget(autofit_item, 4).currentText() == "Auto":
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

    def get_parameter_values(self, peak_number, channel_number=None):
        """Returns a dict of the parameter values of a peak. If
        *channel_number* is given, return a dict of the parameter values of the
        peak for the given channel."""
        if channel_number is None:
            return {"frequency": self.get_frequency(peak_number),
                    "damping": self.get_damping(peak_number),
                    "amplitude": self.get_amplitude(peak_number),
                    "phase": self.get_phase(peak_number)}
        else:
            return \
                {"frequency": self.get_frequency(peak_number, channel_number),
                 "damping": self.get_damping(peak_number, channel_number),
                 "amplitude": self.get_amplitude(peak_number, channel_number),
                 "phase": self.get_phase(peak_number, channel_number)}

    def set_frequency(self, peak_number, channel_number=None, value=0):
        """Set the frequency of a given peak to *value*. If *channel_number* is
        given, set the frequency of the given peak in the given channel."""
        # Get the top level items
        peak_item = self.tree.topLevelItem(peak_number)
        autofit_peak_item = self.autofit_tree.topLevelItem(peak_number)
        # Check they exist
        if peak_item is not None:
            # If they have children
            if channel_number is not None:
                # Get the channel items
                channel_item = peak_item.child(channel_number)
                autofit_channel_item = autofit_peak_item.child(channel_number)
                # Set the value only if the combobox is set to autofit
                combobox = \
                    self.autofit_tree.itemWidget(autofit_channel_item, 1)
                if combobox.currentText() == "Auto":
                    spinbox = self.tree.itemWidget(channel_item, 1)
                    spinbox.setValue(value)
            else:
                # Set the value only if the combobox is set to autofit
                combobox = self.autofit_tree.itemWidget(autofit_peak_item, 1)
                if combobox.currentText() == "Auto":
                    spinbox = self.tree.itemWidget(peak_item, 1)
                    spinbox.setValue(value)

    def set_damping(self, peak_number, channel_number=None, value=0):
        """Set the damping ratio of a given peak to *value*. If *channel_number* is
        given, set the damping ratio of the given peak in the given channel."""
        # Get the top level items
        peak_item = self.tree.topLevelItem(peak_number)
        autofit_peak_item = self.autofit_tree.topLevelItem(peak_number)
        # Check they exist
        if peak_item is not None:
            # If they have children
            if channel_number is not None:
                # Get the channel items
                channel_item = peak_item.child(channel_number)
                autofit_channel_item = autofit_peak_item.child(channel_number)
                # Set the value only if the combobox is set to autofit
                combobox = \
                    self.autofit_tree.itemWidget(autofit_channel_item, 2)
                if combobox.currentText() == "Auto":
                    spinbox = self.tree.itemWidget(channel_item, 2)
                    spinbox.setValue(value)
            else:
                # Set the value only if the combobox is set to autofit
                combobox = self.autofit_tree.itemWidget(autofit_peak_item, 2)
                if combobox.currentText() == "Auto":
                    spinbox = self.tree.itemWidget(peak_item, 2)
                    spinbox.setValue(value)

    def set_amplitude(self, peak_number, channel_number=None, value=0):
        """Set the amplitude of a given peak to *value*. If *channel_number* is
        given, set the amplitude of the given peak in the given channel."""
        # Get the top level items
        peak_item = self.tree.topLevelItem(peak_number)
        autofit_peak_item = self.autofit_tree.topLevelItem(peak_number)
        # Check they exist
        if peak_item is not None:
            # If they have children
            if channel_number is not None:
                # Get the channel items
                channel_item = peak_item.child(channel_number)
                autofit_channel_item = autofit_peak_item.child(channel_number)
                # Set the value only if the combobox is set to autofit
                combobox = \
                    self.autofit_tree.itemWidget(autofit_channel_item, 3)
                if combobox.currentText() == "Auto":
                    spinbox = self.tree.itemWidget(channel_item, 3)
                    spinbox.setValue(value)
            else:
                # Set the value only if the combobox is set to autofit
                combobox = self.autofit_tree.itemWidget(autofit_peak_item, 3)
                if combobox.currentText() == "Auto":
                    spinbox = self.tree.itemWidget(peak_item, 3)
                    spinbox.setValue(value)

    def set_phase(self, peak_number, channel_number=None, value=0):
        """Set the phase of a given peak to *value*. If *channel_number* is
        given, set the phase of the given peak in the given channel."""
        # Get the top level items
        peak_item = self.tree.topLevelItem(peak_number)
        autofit_peak_item = self.autofit_tree.topLevelItem(peak_number)
        # Check they exist
        if peak_item is not None:
            # If they have children
            if channel_number is not None:
                # Get the channel items
                channel_item = peak_item.child(channel_number)
                autofit_channel_item = autofit_peak_item.child(channel_number)
                # Set the value only if the combobox is set to autofit
                combobox = \
                    self.autofit_tree.itemWidget(autofit_channel_item, 4)
                if combobox.currentText() == "Auto":
                    spinbox = self.tree.itemWidget(channel_item, 4)
                    spinbox.setValue(value)
            else:
                # Set the value only if the combobox is set to autofit
                combobox = self.autofit_tree.itemWidget(autofit_peak_item, 4)
                if combobox.currentText() == "Auto":
                    spinbox = self.tree.itemWidget(peak_item, 4)
                    spinbox.setValue(value)

    def set_parameter_values(self, peak_number, channel_number=None,
                             channel_values={}):
        """Set the parameter values for a given peak to those given in
        *channel_values*. If *channel_number* is given, set the values of the
        given peak in the given channel."""
        if "frequency" in channel_values.keys():
            self.set_frequency(peak_number, channel_number,
                               channel_values["frequency"])
        if "damping" in channel_values.keys():
            self.set_damping(peak_number, channel_number,
                             channel_values["damping"])
        if "amplitude" in channel_values.keys():
            self.set_amplitude(peak_number, channel_number,
                               channel_values["amplitude"])
        if "phase" in channel_values.keys():
            self.set_phase(peak_number, channel_number,
                           channel_values["phase"])

if __name__ == '__main__':
    app=0
    app=QApplication(sys.argv)
    w = CircleFitTree()
    w.show()
    sys.exit(app.exec_())
if __name__ == '__main__':
    import sys
    sys.path.append('../')

import numpy as np
from bin.numpy_functions import MatlabList

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout,
                             QLineEdit, QCheckBox, QScrollArea)


class ChannelSelectWidget(QWidget):

    channel_selection_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Create the master layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # # Create the viewbox of checkboxes
        # Create the viewbox
        self.checkbox_viewbox = QWidget(self)
        # Set the layout
        self.viewbox_layout = QVBoxLayout()
        self.checkbox_viewbox.setLayout(self.viewbox_layout)
        # Create a scroll area so that the box can be scrollable
        self.scrollbox = QScrollArea(self)
        self.scrollbox.setWidget(self.checkbox_viewbox)
        self.scrollbox.setWidgetResizable(True)
        # Add the viewbox to the master layout
        self.layout.addWidget(self.scrollbox)

        # # Create the selection toggle buttons
        self.selection_btns_layout = QVBoxLayout()
        self.layout.addLayout(self.selection_btns_layout)

        self.select_all_btn = QPushButton('Select All', self)
        self.select_all_btn.clicked.connect(self.select_all)
        self.select_all_btn.clicked.connect(self.on_channel_selection_change)
        self.selection_btns_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton('Deselect All', self)
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        self.deselect_all_btn.clicked.connect(self.on_channel_selection_change)
        self.selection_btns_layout.addWidget(self.deselect_all_btn)

        self.invert_select_btn = QPushButton('Invert Selection', self)
        self.invert_select_btn.clicked.connect(self.invert_select)
        self.invert_select_btn.clicked.connect(self.on_channel_selection_change)
        self.selection_btns_layout.addWidget(self.invert_select_btn)

        # # Create the text selection box
        self.text_select_box = QLineEdit(self)
        self.text_select_box.returnPressed.connect(self.select_by_text)
        self.selection_btns_layout.addWidget(self.text_select_box)

    def select_all(self):
        self.text_select_box.clear()

        for checkbox in self.checkbox_dict.values():
            checkbox.setChecked(True)

    def deselect_all(self):
       self.text_select_box.clear()

       for checkbox in self.checkbox_dict.values():
            checkbox.setChecked(False)

    def invert_select(self):
        self.text_select_box.clear()

        for checkbox in self.checkbox_dict.values():
            checkbox.toggle()

    def select_by_text(self):
        # Get the text from the box
        string = self.text_select_box.text()
        #print("Selecting by " + string)

        selected_list = []

        # Split the string by commas
        index_list = string.split(",")
        for index in index_list:
            # If it's just a number, add it to the list
            if index.isdigit():
                selected_list.append(int(index))

            # If it's a slice, add the sliced bits to the list
            split_on_colon = index.split(":")
            if len(split_on_colon) > 1:
                # If it's a slice with no step
                if len(split_on_colon) == 2:
                    for i in range(int(split_on_colon[0]),
                                   int(split_on_colon[1]) + 1):
                        selected_list.append(i)
                # If it's a slice with step
                if len(split_on_colon) == 3:
                    for i in range(int(split_on_colon[0]),
                                   int(split_on_colon[1]) + 1,
                                   int(split_on_colon[2])):
                        selected_list.append(i)
            else:
                # Ignore anything else
                continue

        self.deselect_all()

        self.set_selected(selected_list)

    def set_selected(self, list_to_select):
        for channel_num, channel in enumerate(self.cs.channels):
            if channel_num in list_to_select:
                self.checkbox_dict[channel.name].setChecked(True)

        self.on_channel_selection_change()

    def on_channel_selection_change(self):
        # Emit the "Selection changed" signal with a list of channels
        # that are currently selected
        print(self.selected_channels())
        self.channel_selection_changed.emit(self.selected_channels())

    def set_channel_set(self, channel_set):
        self.cs = channel_set

        self.checkbox_dict = {}

        # Clear the old layout
        while self.viewbox_layout.count():
            self.viewbox_layout.takeAt(0).widget().deleteLater()

        for i, channel in enumerate(self.cs.channels):
            # Create a checkbox for this channel
            checkbox = QCheckBox("{}: {}".format(i, channel.name),
                                 self.checkbox_viewbox)
            checkbox.setChecked(True)
            checkbox.clicked.connect(self.on_channel_selection_change)
            # Add it to the dict
            self.checkbox_dict[channel.name] = checkbox
            # Add it to the layout
            self.viewbox_layout.addWidget(self.checkbox_dict[channel.name])

        # Send out a signal with the updated channels
        self.on_channel_selection_change()

    def selected_channels(self):
        """Get a list of channel numbers of all currently selected channels"""
        selected_list = []

        for i, channel in enumerate(self.cs.channels):
            if self.checkbox_dict[channel.name].isChecked():
                selected_list.append(i)

        return selected_list


class ChannelSet():
    """A group of channels, with methods for setting and getting data.

    In theory, a user will only need to interact with the ChannelSet to
    interact with the channels and data. Each ChannelSet will normally be
    derived from one set of results, or one run of an experiment, and then
    the ChannelSet will contain all the information and analysis from that run.
    ChannelSets can be initialised as empty, and channels added later,
    or initialised with a number of empty channels, to which DataSets can be
    added later. Channels are stored in a matlab-style list structure
    (see bin.numpy_functions.MatlabList) which uses tuple indexing, eg.
    channelset.channels[1, 2, range(5,10)], so that multiple channels can be
    selected easily.

    Attributes:
        channels: A MatlabList of the channels in this set.

    Methods:
        add_channels(num_channels=1): Add new empty channels to the end of the
            channel list
        add_channel_dataset(channel_index, id_):  Add an empty dataset with id_
            to the channel(s) specified by channel_index
        set_channel_data(channel_index, id_, data): Set the data in dataset
            with id_ in the channel(s) specified by channel_index
        set_channel_units(channel_index, id_, units): Set the units of dataset
            with id_ in the channel(s) specified by channel_index
        set_channel_metadata(self, channel_index, metadata_dict): Set the
            metadata given in metadata_dict of the channel(s) specified
            by channel_index.
        get_channel_ids(channel_index): Get the ids of all datasets in the
            channel(s) specified by channel_index
        get_channel_data(channel_index, id_): Get the data from dataset
            with id_ in the channel(s) specified by channel_index
        get_channel_units(channel_index, id_): Get the units from dataset
            with id_ in the channel(s) specified by channel_index
        get_channel_metadata(channel_index, metadata_id=None): Get the metadata
            with the name metadata_id from the channel(s) specified by
            channel_index
            """
    def __init__(self, initial_num_channels=0):
        # Initialise the channel list
        self.channels = MatlabList()

        # Create an initial number of channels
        self.add_channels(initial_num_channels)

    def __len__(self):
        return len(self.channels)

    def get_info(self):
        print("ChannelSet: \n Channels: \n")

        for i, channel in enumerate(self.channels):
            print("--------------------\n"
                + "{}    ".format(i))
            channel.get_info()

    def add_channels(self, num_channels=1):
        num = len(self)
        for i in range(num_channels):
            def_name = 'Channel %i' % num
            self.channels.append(Channel(name = def_name))
            num +=1

    def add_channel_dataset(self, channel_index, id_, data=None, units=None):
        """Add an empty dataset to the specified channel(s)"""
        # If an tuple is given, indexing the channels will give an iterable,
        # otherwise it will give one result
        if isinstance(channel_index, tuple):
            for channel in self.channels[channel_index]:
                channel.add_dataset(id_)
        else:
            self.channels[channel_index].add_dataset(id_)

        if data is not None:
            self.set_channel_data(channel_index, id_, data)
        if units is not None:
            self.set_channel_units(channel_index, id_, units)

    def set_channel_data(self, channel_index, id_, data):
        """Set the data in a dataset in the specified channel(s)"""
        # If an tuple is given, indexing the channels will give an iterable,
        # otherwise it will give one result
        if isinstance(channel_index, tuple):
            for channel in self.channels[channel_index]:
                channel.set_data(id_, data)
        else:
            self.channels[channel_index].set_data(id_, data)

    def set_channel_units(self, channel_index, id_, units):
        """Set the units of a dataset in the specified channel(s)"""
        # If an tuple is given, indexing the channels will give an iterable,
        # otherwise it will give one result
        if isinstance(channel_index, tuple):
            for channel in self.channels[channel_index]:
                channel.set_units(id_, units)
        else:
            self.channels[channel_index].set_units(id_, units)

    def set_channel_metadata(self, channel_index, metadata_dict):
        """Set specified metadata of specified channel(s)"""
        # If an tuple is given, indexing the channels will give an iterable,
        # otherwise it will give one result
        if isinstance(channel_index, tuple):
            # Iterate through the given channels
            for channel in self.channels[channel_index]:
                # Get metadata from this channel
                channel.set_metadata(metadata_dict)
        else:
            # Get metadata from this channel
            self.channels[channel_index].set_metadata(metadata_dict)

    def get_channel_ids(self, channel_index):
        """Get the ids of all datasets in channel(s)"""
        # If an tuple is given, indexing the channels will give an iterable,
        # otherwise it will give one result
        if isinstance(channel_index, tuple):
            #output = []
            # Iterate through the given channels
            #for channel in self.channels[channel_index]:
                # Get metadata from this channel
                #output.append(channel.get_ids())
            #return output
            return [chan.get_ids() for chan in self.channels[channel_index]]
        else:
            # Get metadata from this channel
            return self.channels[channel_index].get_ids()

    def get_channel_data(self, channel_index, id_):
        """Get specified data from specified channel(s)"""
        # If an tuple is given, indexing the channels will give an iterable,
        # otherwise it will give one result
        if isinstance(channel_index, tuple):
            #for channel in self.channels[channel_index]:
            return [chan.get_data(id_) for chan in self.channels[channel_index]]
        else:
            return self.channels[channel_index].get_data(id_)

    def get_channel_units(self, channel_index, id_):
        """Get specified units from specified channel(s)"""
        # If an int is given, indexing the channels will give one result,
        # otherwise it will give an iterable
        if isinstance(channel_index, tuple):
            #for channel in self.channels[channel_index]:
            return [chan.get_units(id_) for chan in self.channels[channel_index]]
        else:
            return self.channels[channel_index].get_units(id_)

    def get_channel_metadata(self, channel_index, metadata_id=None):
        """Get specified metadata from specified channel(s)"""
        # If an int is given, indexing the channels will give one result,
        # otherwise it will give an iterable
        if isinstance(channel_index, tuple):
            # Iterate through the given channels
            #for channel in self.channels[channel_index]:
                # Get metadata from this channel
            return [chan.get_metadata(metadata_id) for chan in self.channels[channel_index]]
                #return channel.get_metadata(metadata_id)
        else:
            # Get metadata from this channel
            return self.channels[channel_index].get_metadata(metadata_id)


class Channel():
    """Contains a group of DataSets and associated metadata.

    Channels are the basic structure used throughout the Datalogger. Channels
    may contain many DataSets, but each must have a unique id_ (ie. cannot have
    two 'time' DataSets). Typically a Channel will be initialised with just
    'time_series' data, and other DataSets will be added as analysis is
    performed - eg. a Fourier Transform produces a 'spectrum' DataSet.
    Channels also contain metadata about the data.

    Attributes:
        name: A human-readable string identifying this channel (eg. 'Input 0',
            or 'Left Accelerometer')
        datasets: A python list of this Channel's DataSets
        comments: A string for any additional comments
        tags: A list of tags (eg. ['accelerometer', 'input']) for quick
            selection and sorting
        sample_rate: The rate (in Hz) that the data was sampled at
        calibration_factor: #TODO#
        transfer_function_type: either 'displacement', 'velocity', or
            'acceleration' - indicates what type of transfer function is stored

    Methods:
        is_dataset(id_): Return a boolean of whether the dataset given by id_
            exists already
        add_dataset(id_, units, data): Create a new dataset in this channel
            with id_, units, data, unless a dataset given by id_ exists
        set_data(id_, data): Set the data in dataset id_
        set_units(id_, units): Set the units of dataset id_
        set_metadata(metadata_dict): Sets the channel metadata as given by
            metadata_dict
        get_ids: Get a list of the datasets that this channel has
        get_data(id_): Get the data in dataset id_
        get_units(id_): Get the units of dataset id_
        get_metadata(): Returns a dict of metadata of this channel

    """
    def __init__(self, name='', datasets=[],
                 comments='',
                 tags=[],
                 sample_rate=1,
                 calibration_factor=1,
                 transfer_function_type="displacement"):

        # Set the channel metadata
        self.name = name
        self.comments = comments
        self.tags = tags
        self.sample_rate = sample_rate
        self.calibration_factor = calibration_factor
        self.transfer_function_type = transfer_function_type
        self.datasets = []

        # Create the auto-generated datasets
        self.add_dataset("time", 's')
        self.add_dataset("frequency", 'Hz')
        self.add_dataset("omega", 'rad')

        # Set the channel datasets
        for ds in datasets:
            self.add_dataset(ds.id_, ds.units, ds.data)

        self.update_autogenerated_datasets()

    def get_info(self):
        print("""Name: {}
        DataSets: {}

        Metadata:
            sample_rate: {}
            calibration_factor: {}
            transfer_function_type: {}

            tags: {}
            comments: {}
        """.format(self.name,
                    self.get_ids(),
                    self.sample_rate,
                    self.calibration_factor,
                    self.transfer_function_type,
                    self.tags,
                    self.comments))

    def is_dataset(self, id_):
        # Return a boolean of whether that dataset exists already
        return any([ds.id_ == id_ for ds in self.datasets])

    def add_dataset(self, id_, units=None, data=0):
        # Add as a new DataSet, unless it already exists
        if not self.is_dataset(id_):
            self.datasets.append(DataSet(id_, units, data))
            self.update_autogenerated_datasets()
        else:
            raise ValueError("DataSet '{}' already exists".format(id_))

    def set_data(self, id_, data):
        # Set the data for a pre-existing DataSet
        for ds in self.datasets:
            if ds.id_ == id_:
                ds.set_data(data)
                self.update_autogenerated_datasets()
                return
        raise ValueError("No such DataSet '{}'".format(id_))

    def set_units(self, id_, units):
        # Set the units for a pre-existing DataSet
        for ds in self.datasets:
            if ds.id_ == id_:
                ds.set_units(units)
                return
        raise ValueError("No such DataSet '{}'".format(id_))

    def set_metadata(self, metadata_dict):
        for metadata_name, metadata_value in metadata_dict.items():
            # If a permitted item of metadata is given, set metadata
            if hasattr(self, metadata_name):
                setattr(self, metadata_name, metadata_value)
            else:
                raise ValueError("No such metadata '{}'".format(metadata_name))

    def get_dataset(self, id_):
        for ds in self.datasets:
            if ds.id_ == id_:
                return ds
        raise ValueError("No such DataSet {}".format(id_))

    def get_ids(self):
        # Get a list of the datasets that this channel has
        return [ds.id_ for ds in self.datasets]

    def get_data(self, id_):
        # Get the data from the DataSet given by id_
        for ds in self.datasets:
            if ds.id_ == id_:
                return ds.data
        raise ValueError("No such DataSet {}".format(id_))

    def get_units(self, id_):
        # Get the units from the DataSet given by id_
        for ds in self.datasets:
            if ds.id_ == id_:
                return ds.units
        raise ValueError("No such DataSet {}".format(id_))

    def get_metadata(self, metadata_id=None):
        metadata_dict = {"name": self.name,
                         "comments": self.comments,
                         "tags": self.tags,
                         "sample_rate": self.sample_rate,
                         "calibration_factor": self.calibration_factor,
                         "transfer_function_type": self.transfer_function_type}
        if metadata_id is None:
            return metadata_dict
        else:
            for key, value in metadata_dict.items():
                    if key == metadata_id:
                        return value

    def update_autogenerated_datasets(self):
        if self.is_dataset("time_series"):
            t = self.get_dataset("time")
            t.set_data(np.linspace(0, self.get_data("time_series").size / self.sample_rate, self.get_data("time_series").size))
        if self.is_dataset("spectrum"):
            f = self.get_dataset("frequency")
            f.set_data(np.linspace(0, self.sample_rate, self.get_data("spectrum").size))
            w = self.get_dataset("omega")
            w.set_data(self.get_data("frequency") * 2*np.pi)


class DataSet():
    """A simple data storage class.

    A DataSet is the basic unit for data storage - a named 1d vector with units

    Attributes:
        id_: A lower-case string containing the name of the data stored in the
            vector - eg. 'time_series', or 'spectrum'
        units: The SI unit in which data are measured
        data: A numpy array of data points associated with id_

    Methods:
        set_id_: set the DataSet's id_
        set_units: set the DataSet's units
        set_data: set the DataSet data
    """
    def __init__(self, id_, units=None, data=0):
        self.set_id(id_)
        self.set_units(units)
        self.set_data(data)

    def set_id(self, id_):
        # Check that the user has input a permitted id_ type
        if isinstance(id_, str):
            self.id_ = id_
        else:
            raise TypeError("'id_' must be a string type.")

    def set_data(self, data):
        # Set the dataset data
        self.data = np.asarray(data)

    def set_units(self, units):
        self.units = units

if __name__ == '__main__':
    from bin.file_import import import_from_mat
    from PyQt5.QtWidgets import QApplication
    app = 0
    app = QApplication(sys.argv)

    cs = ChannelSet()
    import_from_mat("//cued-fs/users/general/tab53/ts-home/Documents/owncloud/Documents/urop/labs/4c6/transfer_function_grid.mat", cs)

    w = ChannelSelectWidget()
    w.set_channel_set(cs)

    w.show()

    sys.exit(app.exec_())


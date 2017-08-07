import numpy as np
from numpy_functions import MatlabList

'''
The idea of this class is that users will only need to interact with
the ChannelSet class to interact with the rest of the class
'''
'''
Usage:
    ChannelSet is a class to contain Channel classes which contains all the
    information of a channel. This is stored in a numpy array.

    When initialising, you can put in an optional argument to initiate a number
    of channel. For example:
        cs = ChannelSet(2) will initiate two Channel class in itself
        cs = ChannelSet() will have no Channel class initiated

    Each Channel will be given a number as an id. For now, it is the channel
    number. (Not sure if this is useful)

    You may initiate more channel later by calling add_channel with an id as
    input, as such:
        cs.add_channel(5) adds a Channel with id of 5 to the array

    To make use of the Channel, you must first add DataSet to the Channel
    to contain the relevant datas, then set the data into that DataSet

    For example, to store a data array of y which is taken from channel 0:
        cs.chan_add_dataset('y', num = 0)
        cs.chan_set_data('y', y, num = 0)

    In chan_add_dataset, the first input argument ('y') is the "name" given
    to that DataSet. In this case, it is known as 'y'. Just like before,
    an optional argument 'num' can be provided to indicated which specific
    channel to add the DataSet to. In this case, it's Channel 0.

    chan_set_data inputs are similar, only with an additional input argument
    which is the value to set to the DataSet

    Multiple DataSets can be added at once by giving a list:
        cs.chan_add_dataset(['x','y','z'])

    However, only one DataSet can be set at once. (Possible improvements here)
    Each DataSet must have a unique id.

    To get data from the DataSets:
        cs.chan_get_data('x',num =[0,2])
    will get the data from 'x' DataSet of Channels 0 and 2

    You can obtain multiple DataSets like so:
        cs.chan_get_data(['x','y'])

    The return value will be a dictionary in this format:
        { <chan_num>: {<DataSet id>: <value>,
                       <DataSet id>: <value>,
                       ...},
          <chan_num>: {<DataSet id>: <value>,
                       <DataSet id>: <value>,
                       ...},
          ...
        }

    So, cs.chan_get_data('y',num = range(2)) will give:
        {0: {'y': array(None, dtype=object)},
         1: {'y': array(None, dtype=object)}}
    In this case, 'y' is a Numpy Array containing None

    The Channel class also contains metadata, which are created
    during initialisation.
    Currently, user-defined metadata are not allowed
    The available metadata are:
        name, cal_factor, units, tags, and comments


    Getting and Setting Metadata is similar to that of DataSets.
    To get metadata:
        cs.chan_get_metadatas(['comments','name','units'],num = range(2))
    returns a dictionary:
        {0: {'comments': '', 'name': 'lol', 'units': 'm/s'},
         1: {'comments': '', 'name': 'Channel 1', 'units': 'm/s'}}

    To set metadata, a dictionary must be provided as such:

        meta_dict = {'name': 'Broken Channel',
                     'comments': 'Don't use this channel'}

        cs.chan_set_metadatas(meta_dict,num = 0)

        cs.chan_get_metadatas(['comments','name','units'],num = range(2))
    now returns:
        {0: {'comments': "Don't use this channel", 'name': 'Broken Channel', 'units': 'm/s'},
         1: {'comments': '', 'name': 'Channel 1', 'units': 'm/s'}}

'''
class ChannelSet():
    """A group of channels, normally made from one recording"""
    def __init__(self, initial_num_channels=0):
        # Initialise the channel list
        self.chans = MatlabList()

        # Create an initial number of channels
        self.add_channels(initial_num_channels)

    def __len__(self):
        return len(self.chans)

    def add_channels(self, num_channels=1):
        for i in range(num_channels):
            self.chans.append(Channel())

    def add_channel_dataset(self, channel_index, id_):
        """Add an empty dataset to the specified channel(s)"""
        # If an int is given, indexing the chans will give one result,
        # otherwise it will give an iterable
        if isinstance(channel_index, int):
            self.chans[channel_index].add_dataset(id_)
        else:
            for channel in self.chans[channel_index]:
                channel.add_dataset(id_)

    def set_channel_data(self, channel_index, id_, data):
        """Set the data in a dataset in the specified channel(s)"""
        # If an int is given, indexing the chans will give one result,
        # otherwise it will give an iterable
        if isinstance(channel_index, int):
            self.chans[channel_index].set_data(id_, data)
        else:
            for channel in self.chans[channel_index]:
                channel.set_data(id_, data)

    def set_channel_units(self, channel_index, id_, units):
        """Set the units of a dataset in the specified channel(s)"""
        # If an int is given, indexing the chans will give one result,
        # otherwise it will give an iterable
        if isinstance(channel_index, int):
            self.chans[channel_index].set_units(id_, units)
        else:
            for channel in self.chans[channel_index]:
                channel.set_units(id_, units)

    def set_channel_metadata(self, channel_index, metadata_dict):
        """Set specified metadata of specified channel(s)"""
        # If an int is given, indexing the chans will give one result,
        # otherwise it will give an iterable
        if isinstance(channel_index, int):
            # Get metadata from this channel
            self.chans[channel_index].set_metadata(metadata_dict)
        else:
            # Iterate through the given channels
            for channel in self.chans[channel_index]:
                # Get metadata from this channel
                channel.set_metadata(metadata_dict)

    def get_channel_ids(self, channel_index):
        # If an int is given, indexing the chans will give one result,
        # otherwise it will give an iterable
        if isinstance(channel_index, int):
            # Get metadata from this channel
            self.chans[channel_index].get_ids()
        else:
            output = []
            # Iterate through the given channels
            for channel in self.chans[channel_index]:
                # Get metadata from this channel
                output.append(channel.get_ids())
            return output

    def get_channel_data(self, channel_index, id_):
        """Get specified data from specified channel(s)"""
        # If an int is given, indexing the chans will give one result,
        # otherwise it will give an iterable
        if isinstance(channel_index, int):
            self.chans[channel_index].get_data(id_)
        else:
            for channel in self.chans[channel_index]:
                channel.get_data(id_)

    def get_channel_units(self, channel_index, id_):
        """Get specified units from specified channel(s)"""
        # If an int is given, indexing the chans will give one result,
        # otherwise it will give an iterable
        if isinstance(channel_index, int):
            self.chans[channel_index].get_units(id_)
        else:
            for channel in self.chans[channel_index]:
                channel.get_units(id_)

    def get_channel_metadata(self, channel_index, metadata_id=None):
        """Get specified metadata from specified channel(s)"""
        # If an int is given, indexing the chans will give one result,
        # otherwise it will give an iterable
        if isinstance(channel_index, int):
            # Get metadata from this channel
            self.chans[channel_index].get_metadata(metadata_id)
        else:
            # Iterate through the given channels
            for channel in self.chans[channel_index]:
                # Get metadata from this channel
                channel.get_metadata(metadata_id)


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
                 calibration_factor=1):

        # Set the channel metadata
        self.name = name
        self.comments = comments
        self.tags = tags
        self.sample_rate = sample_rate
        self.calibration_factor = calibration_factor

        # Set the channel datasets
        self.datasets = []
        for ds in datasets:
            self.add_dataset(ds.id_, ds.units, ds.data)

    def is_dataset(self, id_):
        # Return a boolean of whether that dataset exists already
        return any([ds.id_ == id_ for ds in self.datasets])

    def add_dataset(self, id_, units=None, data=0):
        # Add as a new DataSet, unless it already exists
        if not self.is_dataset(id_):
            self.datasets.append(DataSet(id_, units, data))
        else:
            raise ValueError("DataSet {} already exists".format(id_))

    def set_data(self, id_, data):
        # Set the data for a pre-existing DataSet
        for ds in self.datasets:
            if ds.id_ == id_:
                ds.set_data(data)
                return
        raise ValueError("No such DataSet {}".format(id_))

    def set_units(self, id_, units):
        # Set the units for a pre-existing DataSet
        for ds in self.datasets:
            if ds.id_ == id_:
                ds.set_units(units)
                return
        raise ValueError("No such DataSet {}".format(id_))

    def set_metadata(self, metadata_dict):
        for metadata_name, metadata_value in metadata_dict.items():
            # If a permitted item of metadata is given, set metadata
            if hasattr(self, metadata_name):
                setattr(self, metadata_name, metadata_value)
            else:
                raise ValueError("No such metadata {}".format(metadata_name))

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
                         "sample rate": self.sample_rate,
                         "calibration factor": self.calibration_factor}
        if metadata_id is None:
            return metadata_dict
        else:
            for key, value in metadata_dict.items():
                    if key == metadata_id:
                        return value


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

import numpy as np


class DataSet():
    """The class for storing data in"""
    def __init__(self,
                 id_=None,
                 values=None):
        self.id_ = str(id_)
        self.values = np.asarray(values)
    
    def set_id_(self, id_):
        self.id_ = str(id_)
    
    def set_values(self, values):
        self.values = np.asarray(values)
        
        
class Channel():
    """The class for storing a channel in"""
    def __init__(self,
                 cid,
                 name=None,
                 datasets=None,
                 values=None,
                 id_=None):
        self.cid = int(cid)
        self.name = name
        self.datasets = np.empty((0), dtype=DataSet)
        if datasets is not None:
            for dataset in datasets:
                self.add_dataset(dataset)
        
        if values:
            self.add_dataset(DataSet(id_, values))
      
    def add_dataset(self, dataset):
        self.datasets = np.append(self.datasets, dataset)

    def set_data(self, id_, values):
        for d in self.datasets:
            if d.id_ == id_:
                d.values = values
                
    def data(self, id_):
        for d in self.datasets:
            if d.id_ == id_:
                return d.values

class ChannelSet():
    """The class for storing a set of channels in"""
    def __init__(self,
                 channels=None):
        if channels is None:
            self.chans = np.empty(0, dtype=Channel)
        else:
            self.chans = np.asarray(channels, dtype=Channel)
    
    def add_channel(self, channel):
        self.chans = np.append(self.chans, channel)
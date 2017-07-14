import numpy as np

class Channel():
    """The class for storing a channel in"""
    def __init__(self,
                 name=None,
                 data=None):
        self.name = name
        self.data = data

class ChannelSet():
    """The class for storing a set of channels in"""
    def __init__(self,
                 num_channels=0,
                 channels=np.empty(0, dtype=Channel)):
        self.channels = channels
        self.num_channels = self.channels.shape[0]
    
    def add_channel(self, channel):
        self.channels = np.append(self.channels, channel)
        self.num_channels += 1
    
    def new_channel(self, data, name=None):
        new_c = Channel(name, np.asarray(data))
        self.add_channel(new_c)
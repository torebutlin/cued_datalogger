import numpy as np
from collections.abc import Sequence
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
    """The class for storing a set of channels in"""
    def __init__(self, channels=None):
        self.chans = np.empty(0, dtype=Channel)
        
        # Add the number of channels, if specified
        if channels:
            for i in range(channels):
                self.add_channel(i)
                
    # Add a Channel with the input cid
    def add_channel(self,cid):
        # TODO: allow inputs of a Channel class????(Probably not)
        self.chans = np.append(self.chans, Channel(cid))
    
    # Add DataSet(s) to Channels specified, all if None
    def chan_add_dataset(self,id_,num = None):
        if isinstance(id_,str) :
           id_ = [id_]
        if num == None:
            num = range(len(self))
        if not isinstance(num,Sequence):
            num = [num]  
        all_val = [None]*len(id_)
        
        num = set(num).intersection(set(range(len(self))))
        for n in num:    
            for d,v in zip(id_,all_val): 
                self.chans[n].add_dataset(d,v)
   
    # Set the data of a DataSet in a Channel
    def chan_set_data(self,id_,value,num = None):
        if num == None:
            num = range(len(self))
        if not isinstance(num,Sequence):
            num = [num]
            
        num = set(num).intersection(set(range(len(self))))
        for n in num:
            self.chans[n].set_data(id_,value)
            
    # Get specified DataSet in specified Channels     
    def chan_get_data(self,id_,num = None):
        if num == None:
            num = range(len(self))
        if not isinstance(num,Sequence):
            num = [num]            
        if isinstance(id_,str):
            id_ = [id_]
        
        num = set(num).intersection(set(range(len(self))))
        chan_datasets = {}
        for n in num:
            if n>= len(self):
                continue
            chan_data = {}
            for d in id_: 
                data,status = self.chans[n].data(d)
                if status:
                    chan_data[d] = data
            chan_datasets[n] = chan_data
            
        return chan_datasets       
    
    # Get the metadatas of specified Channels
    def chan_get_metadatas(self,meta_names,num = None): 
        metadatas = {}
        if num == None:
            num = range(len(self))
        if not isinstance(num,Sequence):
            num = [num]
        
        if isinstance(meta_names,str):
            meta_names = [meta_names]
            
        num = set(num).intersection(set(range(len(self))))
            
        for n in num:
            mdata = {}
            for m in meta_names:
                md,status = self.chans[n].get_metadata(m.lower())
                if status:
                    mdata[m.lower()] = md
            metadatas[n] = mdata
        
        return metadatas
    
    # Get the metadatas of specified Channels
    def chan_set_metadatas(self,meta_dict,num = None):
        if not type(meta_dict) == dict:
            raise Exception('Please Enter a Dictionary type')
        
        if num == None:
            num = range(len(self))
        if not isinstance(num,Sequence):
            num = [num]
            
        num = set(num).intersection(set(range(len(self))))
        for n in num:
            for m,v in zip(iter(meta_dict.keys()),iter(meta_dict.values())):
                    self.chans[n].set_metadata(m.lower(),v)
                
    def __len__(self):
        return(len(self.chans))
    
class Channel():
    """The class for storing a channel in"""
    def __init__(self,cid,name=None,
                 datasets=None,values=None,id_=None):
        
        # Metadata here
        self.cid = int(cid)
        if name == None:
            self.name = 'Channel %i' % cid
        else:
            self.name = str(name)
        self.cal_factor = 1
        self.units = 'm/s'
        self.tags = []
        self.comments = ''
        
        # DataSets here
        self.datasets = np.empty((0), dtype=DataSet)
        if datasets is not None:
            for dataset in datasets:
                self.add_dataset(dataset)
        
        if values:
            self.add_dataset(DataSet(id_, values))
    
    def available_datasets(self):
        return [ds.id_ for ds in self.datasets]
    
    def is_dataset(self,id_):
        return any([ds.id_ == id_ for ds in self.datasets])
    
    def add_dataset(self, id_ ,values=None):
        if not self.is_dataset(id_):
            self.datasets = np.append(self.datasets, DataSet(id_,values))
        else:
            print('You already have that dataset!')
            
    def set_data(self, id_, values):
        for ds in self.datasets:
            if ds.id_ == id_:
                ds.set_values(values)
                return
        print('No such datasets')    
            
    def data(self, id_):
        for ds in self.datasets:
            if ds.id_ == id_:
                return ds.values,True
        print('No such datasets')
        return None,False
    
    def get_metadata(self,meta_name):
        if hasattr(self,meta_name):
            return getattr(self,meta_name),True
        else:
            print('No such attribute')
            return None,False
    
    def set_metadata(self,meta_name,val):
        if hasattr(self,meta_name):
                setattr(self,meta_name,val)

class DataSet():
    """The class for storing data in"""
    def __init__(self,id_,values=None):
        self.id_ = str(id_)
        self.values = np.asarray(values)
    
    def set_id_(self, id_):
        self.id_ = str(id_)
    
    def set_values(self, values):
        self.values = np.asarray(values)
        
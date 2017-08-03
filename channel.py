import numpy as np

class ChannelSet():
    """The class for storing a set of channels in"""
    def __init__(self, channels=None):
        self.chans = np.empty(0, dtype=Channel)
        
        if channels:
            for i in range(channels):
                self.add_channel(i)
    
    def add_channel(self,cid):
        self.chans = np.append(self.chans, Channel(cid))
        
    def get_metadatas(self,meta_names,chan_nums): 
        metadatas = {}
        if type(chan_nums) == int: 
            chan_nums = (chan_nums)
        if type(meta_names) == str:
            meta_names = (meta_names)

        for n in chan_nums:
            mdata = {}
            for m in meta_names:
                mdata[m.lower()] = self._get_chan_metadata(m.lower(),n)
            metadatas[str(n)] = mdata
            
        return metadatas
    
    def set_metadatas(self,meta_names,chan_nums,val): 
        if type(chan_nums) == int: 
            chan_nums = [chan_nums]
        if type(meta_names) == str:
            meta_names = [meta_names]
            
        for n in chan_nums:
            for m,v in zip(meta_names,val):
                self._set_chan_metadata(m.lower(),n,v)

    
    def _get_chan_metadata(self,meta_name,chan_num):
        mdata = None
        try:
            if hasattr(self.chans[chan_num],meta_name):
                mdata = getattr(self.chans[chan_num],meta_name)
            else:
                raise ('No such attribute')
        except IndexError:
            print('The specified channel cannot be found')
            
        return mdata
    
    def _set_chan_metadata(self,meta_name,chan_num,val):
        try:
            
                setattr(self.chans[chan_num],meta_name,val)
        except IndexError:
            print('The specified channel cannot be found')
    
    def __len__(self):
        return(len(self.chans))
    
class Channel():
    """The class for storing a channel in"""
    def __init__(self,cid,name=None,
                 datasets=None,values=None,id_=None):
        
        # Put metadata here
        self.cid = int(cid)
        self.name = name
        self.cal_factor = 1
        self.units = 'm/s'
        self.tags = []
        self.comments = ''
        
        # Put data here
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
        
        

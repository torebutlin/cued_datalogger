import numpy as np
'''
The idea of this class is that users will only need to interact with
the ChannelSet class to interact with the rest of the class
'''

class ChannelSet():
    """The class for storing a set of channels in"""
    def __init__(self, channels=None):
        self.chans = np.empty(0, dtype=Channel)
        
        if channels:
            for i in range(channels):
                self.add_channel(i)
                
    # Add a Channel
    # TODO: allow inputs of a Channel class????
    def add_channel(self,cid):
        self.chans = np.append(self.chans, Channel(cid))
    
    # Add a DataSet to Channel
    def chan_add_dataset(self,id_,num = None, value = None):
        if type(id_) == str:
            id_ = [id_]
        if num == None:
            num = range(len(self))
        if type(num) == int:
            num = [num]  
        all_val = []
        try:
            all_val.extend(value)
            if len(all_val)<len(id_):
                all_val.extend([None]*(len(id_)-len(all_val)))
        except TypeError:
            all_val.append(value)
            all_val = all_val*len(id_)  
            
        for n in num:    
            for d,v in zip(id_,all_val): 
                self.chans[n].add_dataset(d,v)
   
    # Set the data of a DataSet in a Channel
    def chan_set_data(self,id_,value,num = None):
        if type(id_) == str:
            id_ = [id_]
        if num == None:
            num = range(len(self))
            value = [value]*len(id_)
        if type(num) == int:
            num = [num]
        all_val = []
        try:
            all_val.extend(value)
        except TypeError:
            all_val.append(value)
        if len(all_val)<len(id_):
            all_val.extend([None]*(len(id_)-len(all_val)))
            
        for n in num: 
            for d,v in zip(id_,all_val): 
                self.chans[n].set_data(d,v)
            
    def chan_get_data(self,id_,num = None):
        if num == None:
            num = range(len(self))
        if type(num) == int:
            num = [num]            
        if type(id_) == str:
            id_ = [id_]
        chan_datasets = {}
        for n in num:
            chan_data = {}
            for d in id_: 
                chan_data[d] = self.chans[n].data(d)
            chan_datasets[str(n)] = chan_data
            
        return chan_datasets       
    
    # Get the metadatas of specified Channels
    def chan_get_metadatas(self,meta_names,num = None): 
        metadatas = {}
        if num == None:
            num = range(len(self))
        if type(num) == int:
            num = [num]
        
        if type(meta_names) == str:
            meta_names = [meta_names]
            
        for n in num:
            mdata = {}
            for m in meta_names:
                try:
                    mdata[m.lower()] = self.chans[n].get_metadata(m.lower())
                except IndexError:
                    print('The specified channel cannot be found')
            metadatas[str(n)] = mdata
        
        return metadatas
    
    # Get the metadatas of specified Channels
    def chan_set_metadatas(self,meta_dict,num = None):
        if not type(meta_dict) == dict:
            raise Exception('Please Enter a Dictionary type')
        
        if num == None:
            num = range(len(self))
        if type(num) == int:
            num = [num]
        else:    
            num = list(set(num))
            num.sort()
        
        for n in num:
            try:
                self.chans[n]
            except IndexError:
                print('The specified channel cannot be found')
                break
            for m,v in zip(iter(meta_dict.keys()),iter(meta_dict.values())):
                    self.chans[n].set_metadata(m.lower(),v)
                
    def __len__(self):
        return(len(self.chans))
    
class Channel():
    """The class for storing a channel in"""
    def __init__(self,cid,name=None,
                 datasets=None,values=None,id_=None):
        
        # Put metadata here
        self.cid = int(cid)
        if name == None:
            self.name = 'Channel %i' % cid
        else:
            self.name = str(name)
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
                return ds.values
            
        print('No such datasets')
    
    def get_metadata(self,meta_name):
        mdata = None
        if hasattr(self,meta_name):
            mdata = getattr(self,meta_name)
        else:
            print('No such attribute')
            
        return mdata
    
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
        
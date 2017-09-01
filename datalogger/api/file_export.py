# -*- coding: utf-8 -*-
"""
Created on Fri Sep  1 14:00:14 2017

@author: eyt21
"""

import scipy.io as sio
from datalogger.api.channel import ChannelSet
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout,QPushButton,QLabel,QListWidget,
                             QTreeWidgetItem,QHBoxLayout,QFileDialog)
from PyQt5.QtCore import  Qt


def export_to_mat(file,order, channel_set=None):
    """
    Export data and metadata from ChannelsSet to a mat file
    
    Parameters
    ----------
    file : path_to_file
        The path to the ``.mat`` file to import data from.
    order : int
        Order of the channel saved
    channel_set : ChannelSet
        The ChannelSet to save the imported data and metadata to. If ``None``, 
        a new ChannelSet is created and returned.
    """
    if channel_set is None:
        new_channel_set = True
        channel_set = ChannelSet(len(order))
    else:
        new_channel_set = False
    
    variables = {}
    data_ids = channel_set.get_channel_ids(order)
    var_names = set([y for x in data_ids for y in x])
    meta_names = cs.get_channel_metadata(0)
    for name in var_names:
        data = channel_set.get_channel_data(order,name)
        variables[name] = data
    for mname in meta_names:
        mdata = channel_set.get_channel_metadata(order,mname)
        variables[mname] = mdata    
    print(variables)
    # Save the variable dict as matlab file 
    file = sio.savemat(file,variables)
    
    if new_channel_set:
        return channel_set
            
class DataExportWidget(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self.cs = ChannelSet()
        self.order = list(range(len(self.cs)))
        self.init_UI()
        
    def init_UI(self):
        layout = QVBoxLayout(self)
        
        self.channel_listview = QListWidget(self)
        layout.addWidget(self.channel_listview)
        shift_btn_layout = QHBoxLayout()
        self.shift_up_btn = QPushButton('Shift Up',self)
        self.shift_down_btn = QPushButton('Shift Down',self)
        shift_btn_layout.addWidget(self.shift_up_btn )
        shift_btn_layout.addWidget(self.shift_down_btn )
        self.mat_export_btn = QPushButton('Export as MAT',self)
        
        layout.addWidget(QLabel('ChannelSet Saving Order',self))
        layout.addWidget(self.channel_listview)
        layout.addLayout(shift_btn_layout)
        layout.addWidget(self.mat_export_btn)
        
    def set_channel_set(self, channel_set):
        self.cs = channel_set
        self.order = list(range(len(self.cs)))
        
    def update_list(self):
        pass
        
    def export_files(self):
        pass
        '''
        # Get a list of URLs from a QFileDialog
        url = QFileDialog.getOpenFileNames(self, "Load transfer function", "addons",
                                               "MAT Files (*.mat)")[0]        
        try:
            import_from_mat(url[0], self.new_cs)
        except:
            print('Load failed. Revert to default!')
            import_from_mat("//cued-fs/users/general/tab53/ts-home/Documents/owncloud/Documents/urop/labs/4c6/transfer_function_clean.mat", 
                            self.new_cs)
    
        self.set_channel_set(self.new_cs)
        '''
if __name__ == '__main__':
    cs = ChannelSet(4)
    cs.add_channel_dataset((0,1,2,3),'time_series',np.random.rand(5,1))
    cs.set_channel_metadata(0,{'name':'Nope'})
    cs.set_channel_metadata(1,{'name':'Lol'})
    export_to_mat('test3',(0,1,2,3),cs)


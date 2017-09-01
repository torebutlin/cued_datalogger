# -*- coding: utf-8 -*-
"""
Created on Fri Sep  1 14:00:14 2017

@author: eyt21
"""

import scipy.io as sio
from datalogger.api.channel import ChannelSet
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout,QPushButton,QLabel,QTreeWidget,
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
        self.new_cs = ChannelSet()
        self.init_UI()
        
    def init_UI(self):
        layout = QVBoxLayout(self)
        
        self.import_btn = QPushButton('Import Mat Files',self)
        self.import_btn.clicked.connect(self.import_files)
        layout.addWidget(self.import_btn)
        
        layout.addWidget(QLabel('New ChannelSet Preview',self))
        
        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabels(["Channel Number", "Name", "Units",
                                   "Comments", "Tags", "Sample rate",
                                   "Calibration factor",
                                   "Transfer function type"])
    
        layout.addWidget(self.tree)
        
        self.mat_export_btn = QPushButton('Export as MAT',self)
        layout.addWidget(self.add_data_btn)
        layout.addWidget(self.rep_data_btn)
    '''    
    def set_channel_set(self, channel_set):
        print("Setting channel set...")
        self.tree.clear()

        #self.cs = channel_set

        self.channel_items = []

        for channel_number, channel in enumerate(channel_set.channels):
            # Create a tree widget item for this channel
            channel_item = QTreeWidgetItem(self.tree)
            #channel_item.setFlags(channel_item.flags() | Qt.ItemIsEditable)
            channel_item.setData(0, Qt.DisplayRole, channel_number)
            channel_item.setData(1, Qt.DisplayRole, channel.name)
            channel_item.setData(3, Qt.DisplayRole, channel.comments)
            channel_item.setData(4, Qt.DisplayRole, channel.tags)
            channel_item.setData(5, Qt.DisplayRole, '%.2f' % channel.sample_rate )
            channel_item.setData(6, Qt.DisplayRole, '%.2f' % channel.calibration_factor)
            channel_item.setData(7, Qt.DisplayRole, channel.transfer_function_type)
            # Add it to the list
            self.channel_items.append(channel_item)

            # Create a child tree widget item for each of the channel's datasets
            for dataset in channel.datasets:
                dataset_item = QTreeWidgetItem(channel_item)
                #dataset_item.setFlags(dataset_item.flags() | Qt.ItemIsEditable)
                dataset_item.setData(1, Qt.DisplayRole, dataset.id_)
                dataset_item.setData(2, Qt.DisplayRole, dataset.units)
        print("Done.")
        
    def import_files(self):
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
        
    def clear(self):
        self.new_cs = ChannelSet()
        self.set_channel_set(self.new_cs)
 '''       
if __name__ == '__main__':
    cs = ChannelSet(4)
    cs.add_channel_dataset((0,1,2,3),'time_series',np.random.rand(5,1))
    cs.set_channel_metadata(0,{'name':'Nope'})
    cs.set_channel_metadata(1,{'name':'Lol'})
    export_to_mat('C:\Users\eyt21\test3',(0,1,2,3),cs)


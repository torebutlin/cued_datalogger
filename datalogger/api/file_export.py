# -*- coding: utf-8 -*-
"""
Created on Fri Sep  1 14:00:14 2017

@author: eyt21
"""

import scipy.io as sio
from datalogger.api.channel import ChannelSet
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout,QPushButton,QLabel,QListWidget,
                             QTreeWidgetItem,QHBoxLayout,QFileDialog,QCheckBox)
from PyQt5.QtCore import  Qt


def export_to_mat(file,order, channel_set=None,back_comp = False):
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
    if not back_comp:
        if channel_set is None:
            new_channel_set = True
            channel_set = ChannelSet(len(order))
        else:
            new_channel_set = False
        
        variables = {}
        data_ids = channel_set.get_channel_ids(order)
        var_names = set([y for x in data_ids for y in x])
        meta_names = channel_set.get_channel_metadata(0)
        for name in var_names:
            data = channel_set.get_channel_data(order,name)
            variables[name] = data
        for mname in meta_names:
            mdata = channel_set.get_channel_metadata(order,mname)
            variables[mname] = mdata    
        #print(variables)
        print(file)
        # Save the variable dict as matlab file 
        sio.savemat(file,variables,appendmat = False)
        
        if new_channel_set:
            return channel_set
    else:
        sampling_rate = channel_set.get_channel_metadata(0,'sample_rate')
        calibration_factor = channel_set.get_channel_metadata(0,'calibration_factor')
        time_series_data = np.array(channel_set.get_channel_data(order,'time_series'))
        print(time_series_data)
        n_samples = time_series_data[0].shape[0]
        variables = {'indata':np.transpose(time_series_data),'freq':float(sampling_rate),
                     'dt2' :[float(len(order)),0,0],'buflen':float(n_samples),
                     'tsmax':float(calibration_factor)}
        sio.savemat(file,variables,appendmat = False)
        #TODO: Save FFT and TF
        #TODO: Save Sonogram
        
class DataExportWidget(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self.cs = ChannelSet()
        self.order = list(range(len(self.cs)))
        #self.selection = 0
        self.init_UI()
        
    def init_UI(self):
        layout = QVBoxLayout(self)
        
        self.channel_listview = QListWidget(self)
        layout.addWidget(self.channel_listview)
        shift_btn_layout = QHBoxLayout()
        shift_up_btn = QPushButton('Shift Up',self)
        shift_up_btn.clicked.connect(lambda: self.shift_list('up'))
        shift_down_btn = QPushButton('Shift Down',self)
        shift_down_btn.clicked.connect(lambda: self.shift_list('down'))
        shift_btn_layout.addWidget(shift_up_btn )
        shift_btn_layout.addWidget(shift_down_btn )
        self.back_comp_btn = QCheckBox('Backward Compatibility?',self)
        self.mat_export_btn = QPushButton('Export as MAT',self)
        self.mat_export_btn.clicked.connect(self.export_files)
        
        layout.addWidget(QLabel('ChannelSet Saving Order',self))
        layout.addWidget(self.channel_listview)
        layout.addLayout(shift_btn_layout)
        layout.addWidget(self.back_comp_btn)
        layout.addWidget(self.mat_export_btn)
        
    def set_channel_set(self, channel_set):
        self.cs = channel_set
        self.order = list(range(len(self.cs)))
        #self.selection = 0
        self.update_list()
        self.channel_listview.setCurrentRow(0)
        
    
    def shift_list(self,mode):
        ind = self.channel_listview.currentRow()
        if mode == 'up':
            if not ind == 0:
                self.order[ind-1],self.order[ind] = self.order[ind],self.order[ind-1]
                ind -= 1
        elif mode == 'down':
            if not ind == self.channel_listview.count()-1:
                self.order[ind],self.order[ind+1] = self.order[ind+1],self.order[ind]
                ind += 1
        self.update_list()
        self.channel_listview.setCurrentRow(ind)
    
    def update_list(self):
        self.channel_listview.clear()
        names = self.cs.get_channel_metadata(tuple(self.order),'name')
        full_names = [str(self.order[i])+' : '+names[i] for i in range(len(names))]
        self.channel_listview.addItems(full_names)
        
    def export_files(self):
        # Get save URL from QFileDialog
        url = QFileDialog.getSaveFileName(self, "Export Data", "",
                                           "MAT Files (*.mat)")[0]
        if url:
            if self.back_comp_btn.checkState() == Qt.Checked:
                print('BackComp')
                export_to_mat(url,tuple(self.order), self.cs,back_comp = True)
            else:
                export_to_mat(url,tuple(self.order), self.cs)
        
if __name__ == '__main__':
    cs = ChannelSet(4)
    cs.add_channel_dataset((0,1,2,3),'time_series',np.random.rand(5,1))
    cs.set_channel_metadata(0,{'name':'Nope'})
    cs.set_channel_metadata(1,{'name':'Lol'})
    export_to_mat('btest.mat',(0,1,2,3),cs,True)


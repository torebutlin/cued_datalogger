# -*- coding: utf-8 -*-
"""
Created on Fri Sep  1 14:00:14 2017

@author: eyt21
"""

import scipy.io as sio
from cued_datalogger.api.channel import ChannelSet
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout,QPushButton,QLabel,QListWidget,
                             QTreeWidgetItem,QHBoxLayout,QFileDialog,QCheckBox)
from PyQt5.QtCore import  Qt
from cued_datalogger.api.numpy_extensions import to_dB

def export_to_mat(file,order, channel_set=None,back_comp = False):
    """
    Export data and metadata from ChannelsSet to a mat file.
    Support backward compatibility with the old logger.
    Still in alpha stage.
    
    Parameters
    ----------
    file : path_to_file
        The path to the ``.mat`` file to import data from.
    order : int
        Order of the channel saved
    channel_set : ChannelSet
        The ChannelSet to save the imported data and metadata to. If ``None``, 
        a new ChannelSet is created and returned.
    back_comp: bool
        Whether to export as the old format
    """
    
    if channel_set is None:
        new_channel_set = True
        channel_set = ChannelSet(len(order))
    else:
        new_channel_set = False
    
    # Obtain the ids and metadata names
    data_ids = channel_set.get_channel_ids(order)
    var_names = set([y for x in data_ids for y in x])
    meta_names = channel_set.get_channel_metadata(0)
        
    if not back_comp:
        # Save all the variable names and metadata names as dicts
        variables = {}
        for name in var_names:
            data = channel_set.get_channel_data(order,name)
            variables[name] = data
        for mname in meta_names:
            mdata = channel_set.get_channel_metadata(order,mname)
            variables[mname] = mdata    
        # Save the dict as matlab file 
        sio.savemat(file,variables,appendmat = False)
        
        if new_channel_set:
            return channel_set
    else:
        # Save as the old format, with individual MAT file for each type of data
        sampling_rate = channel_set.get_channel_metadata(0,'sample_rate')
        calibration_factor = channel_set.get_channel_metadata(0,'calibration_factor')
        # Save Time Series
        if 'time_series' in var_names:
            time_series_data = np.array(channel_set.get_channel_data(order,'time_series'))
            n_samples = time_series_data[0].shape[0]
            variables = {'indata':np.transpose(time_series_data),'freq':float(sampling_rate),
                         'dt2' :[float(len(order)),0,0],'buflen':float(n_samples),
                         'tsmax':float(calibration_factor)}
            time_series_fname = file[:-4]+'_TimeSeries.mat'
            sio.savemat(time_series_fname,variables,appendmat = False)
        # Save FFT
        if 'spectrum' in var_names:
            fft_data = np.array(channel_set.get_channel_data(order,'spectrum'))
            n_samples = fft_data[0].shape[0]
            variables = {'yspec':np.transpose(fft_data),'freq':float(sampling_rate),
                         'dt2' :[0,float(len(order)),0],'npts':float((n_samples-1)*2),
                         'tfun':0}
            time_series_fname = file[:-4]+'_FFT.mat'
            sio.savemat(time_series_fname,variables,appendmat = False)
        # Save TF
        if 'TF' in var_names:
            TF_data = np.array(channel_set.get_channel_data(order,'TF'))
            TF_data = [data for data in TF_data if not data.shape[0] == 0]
            n_samples = TF_data[0].shape[0]
            variables = {'yspec':np.transpose(TF_data),'freq':float(sampling_rate),
                         'dt2' :[0,float(len(order)-1),0],'npts':float((n_samples-1)*2),
                         'tfun':1}
            time_series_fname = file[:-4]+'_TF.mat'
            sio.savemat(time_series_fname,variables,appendmat = False)
        # Save Sonogram
        if 'sonogram' in var_names:
            sono_data = channel_set.get_channel_data(order[0],'sonogram')
            if not sono_data.shape[0] == 0:
                sono_phase = channel_set.get_channel_data(order[0],'sonogram_phase')
                sono_step = channel_set.get_channel_data(order[0],'sonogram_step')
                n_samples = sono_data[0].shape[0]
                variables = {'yson':to_dB(np.abs(sono_data)),'freq':float(sampling_rate),
                             'dt2' :[0,0,1],'npts':float((n_samples-1)*2),
                             'sonstep':float(sono_step),'yphase': sono_phase}
                time_series_fname = file[:-4]+'_sonogram.mat'
                sio.savemat(time_series_fname,variables,appendmat = False)
            
class DataExportWidget(QWidget):
    """
    A proof-of-concept widget to show that exporting data is possible.
    Currently, it saves all of the available variables. Alpha stage.
    
    Attributes
    ----------
    cs : ChannelSet
        Reference to the channelSet
    order : list
        The order of channels to be saved    
    """
    def __init__(self,parent):
        super().__init__(parent)
        self.cs = ChannelSet()
        self.order = list(range(len(self.cs)))
        self.init_UI()
        
    def init_UI(self):
        """
        Construct the UI
        """
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
        
        # TODO: Have a preview of what is being saved?
        layout.addWidget(QLabel('ChannelSet Saving Order',self))
        layout.addWidget(self.channel_listview)
        layout.addLayout(shift_btn_layout)
        layout.addWidget(self.back_comp_btn)
        layout.addWidget(self.mat_export_btn)
        
    def set_channel_set(self, channel_set):
        """
        Set the ChannelSet reference
        """
        self.cs = channel_set
        self.order = list(range(len(self.cs)))
        self.update_list()
        self.channel_listview.setCurrentRow(0)
    
    def shift_list(self,mode):
        """
        Shift the channel saving order
        
        Parameter
        ---------
        mode : str
            either 'up' or 'down', indicating the shifting direction
        """
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
        """
        Update the list with the current saving order
        """
        self.channel_listview.clear()
        names = self.cs.get_channel_metadata(tuple(self.order),'name')
        full_names = [str(self.order[i])+' : '+names[i] for i in range(len(names))]
        self.channel_listview.addItems(full_names)
        
    def export_files(self):
        """
        Export the file to the url selected
        """
        url = QFileDialog.getSaveFileName(self, "Export Data", "",
                                           "MAT Files (*.mat)")[0]
        if url:
            if self.back_comp_btn.checkState() == Qt.Checked:
                export_to_mat(url,tuple(self.order), self.cs,back_comp = True)
            else:
                export_to_mat(url,tuple(self.order), self.cs)
        
if __name__ == '__main__':
    cs = ChannelSet(4)
    cs.add_channel_dataset((0,1,2,3),'time_series',np.random.rand(5,1))
    cs.set_channel_metadata(0,{'name':'Nope'})
    cs.set_channel_metadata(1,{'name':'Lol'})
    export_to_mat('btest.mat',(0,1,2,3),cs,True)

